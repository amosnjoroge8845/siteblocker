import ctypes
import json
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765

HOSTS_FILE = Path(
    os.environ.get("SystemRoot", r"C:\Windows")
) / r"System32\drivers\etc\hosts"

START_MARKER = "# SITEBLOCKER START"
END_MARKER = "# SITEBLOCKER END"

# Change this PIN before using the blocker seriously.
PIN = "Amos.cGeSDhuojnhyui?09877juik;okjggvbmnmhhioiklk876766||||||?';.mmmmknnjjnjjklp"

# Secret used by the browser extension when talking to this helper.
TOKEN_FILE = Path(__file__).with_name("token.txt")


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()

    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


TOKEN = get_token()


def clean_domain(domain):
    domain = domain.strip().lower()

    domain = re.sub(r"^https?://", "", domain)
    domain = domain.split("/")[0]
    domain = re.sub(r"^www\.", "", domain)

    # Only allow normal domain names.
    if not re.fullmatch(
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}",
        domain
    ):
        raise ValueError("Invalid domain")

    return domain


def read_hosts():
    if not HOSTS_FILE.exists():
        return []

    return HOSTS_FILE.read_text(
        encoding="ascii",
        errors="ignore"
    ).splitlines()


def write_hosts(lines):
    HOSTS_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="ascii"
    )

    os.system("ipconfig /flushdns >nul 2>&1")


def get_blocked_sites():
    lines = read_hosts()

    sites = []

    inside = False

    for line in lines:

        line = line.strip()

        if line == START_MARKER:
            inside = True
            continue

        if line == END_MARKER:
            inside = False
            continue

        if inside and line.startswith("0.0.0.0 "):
            site = line[8:].strip()

            if site:
                sites.append(site)

    return sites


def update_hosts(sites):
    lines = read_hosts()

    new_lines = []

    inside = False

    for line in lines:

        if line.strip() == START_MARKER:
            inside = True
            continue

        if line.strip() == END_MARKER:
            inside = False
            continue

        if not inside:
            new_lines.append(line)

    new_lines.append("")
    new_lines.append(START_MARKER)

    for site in sorted(set(sites)):
        new_lines.append(f"0.0.0.0 {site}")
        new_lines.append(f"0.0.0.0 www.{site}")

    new_lines.append(END_MARKER)

    write_hosts(new_lines)


class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):

        body = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "chrome-extension://*"
        )

        self.end_headers()

        self.wfile.write(body)

    def do_POST(self):

        if self.path != "/action":
            self.send_json(
                {"error": "Not found"},
                404
            )
            return

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            body = self.rfile.read(length)

            request = json.loads(
                body.decode("utf-8")
            )

            if request.get("token") != TOKEN:
                self.send_json(
                    {"error": "Unauthorized"},
                    401
                )
                return

            action = request.get("action")

            if action == "list":

                self.send_json({
                    "sites": get_blocked_sites()
                })
                return

            if action == "block":

                site = clean_domain(
                    request.get("site", "")
                )

                sites = get_blocked_sites()

                if site not in sites:
                    sites.append(site)

                update_hosts(sites)

                self.send_json({
                    "success": True,
                    "sites": get_blocked_sites()
                })

                return

            if action == "unblock":

                pin = str(
                    request.get("pin", "")
                )

                if pin != PIN:
                    self.send_json(
                        {"error": "Incorrect PIN"},
                        403
                    )
                    return

                site = clean_domain(
                    request.get("site", "")
                )

                sites = get_blocked_sites()

                sites = [
                    s for s in sites
                    if s != site
                ]

                update_hosts(sites)

                self.send_json({
                    "success": True,
                    "sites": get_blocked_sites()
                })

                return

            self.send_json(
                {"error": "Unknown action"},
                400
            )

        except Exception as e:

            self.send_json(
                {"error": str(e)},
                500
            )

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":

    if not is_admin():

        print(
            "ERROR: SiteBlocker Helper must run as Administrator."
        )

        raise SystemExit(1)

    print("SiteBlocker Windows Helper")
    print(f"Listening on http://{HOST}:{PORT}")

    server = HTTPServer(
        (HOST, PORT),
        Handler
    )

    server.serve_forever()