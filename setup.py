# setup.py — Wi-Fi AP + adafruit_httpserver, sert /html, gère /config & /savekey
# Ne s'exécute que si /setup existe (voir code.py -> setup.run(...))

import sys, os, json, time, supervisor, gc
import storage
from password_manager import PasswordManager

SSID = "BiduleBox"
PASS = "Bidule1234"

# ---------- FS helpers ----------
def ensure_rw():
    try:
        storage.remount("/", False)  # False = read/write
    except Exception as e:
        print("[SETUP] remount RW failed:", e)

def _exists(path):
    try:
        os.stat(path); return True
    except OSError:
        return False

def _read_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path, obj):
    ensure_rw()
    with open(path, "w") as f:
        json.dump(obj, f)

def _read_text(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return ""

def _write_text(path, s):
    ensure_rw()
    with open(path, "w") as f:
        f.write(s)

def _validate_buttons(btns):
    out, seen = [], set()
    for b in btns:
        try:
            bid = int(b.get("id", 0))
            if bid <= 0 or bid in seen:
                continue
            seen.add(bid)
            pin = str(b.get("pin", b.get("pin_name", "GP11"))).upper()
            if not pin.startswith("GP"):
                continue
            out.append({
                "id": bid,
                "couleur": str(b.get("couleur", b.get("color", ""))),
                "pin": pin,
                "pin_name": pin,
                "macro": str(b.get("macro", "")),
                "command": str(b.get("command", "")),
                "pass_key": str(b.get("pass_key", "")),
                "winsearch": bool(b.get("winsearch", True)),
                "delay_ms": int(b.get("delay_ms", 1000)),
            })
        except Exception:
            continue
    return out


def run(blink_ok=None, blink_ko=None, led=None, led_red=None):
    def _ok(n):
        if blink_ok: blink_ok(n)
    def _ko(n):
        if blink_ko: blink_ko(n)

    if not _exists("/setup"):
        print("[SETUP] Pas de /setup → sortie.")
        return

    # Import réseau/HTTP uniquement en mode setup
    import wifi
    import socketpool
    from adafruit_httpserver import Server, Request, Response, JSONResponse, FileResponse, GET, POST

    print("[SETUP] Démarrage AP…")
    wifi.radio.start_ap(SSID, PASS)
    ip_ap = wifi.radio.ipv4_address_ap
    print(f"[SETUP] AP ready: SSID={SSID} PASS={PASS} IP={ip_ap}")
    _ok(3)
    if led: led.value = True

    gc.collect()
    time.sleep(0.5)

    pool = socketpool.SocketPool(wifi.radio)
    # Sécurisé: ne sert que /html
    server = Server(pool, root_path="/html")  # DO NOT expose publicly

    # ---------- Routes API & système ----------
    @server.route("/", [GET])
    def index(req: Request):
        if _exists("/html/index.html"):
            # Chemin relatif à root_path (/html)
            return FileResponse(req, "/index.html")
        return Response(req, "index.html manquant (placer dans /html/)", content_type="text/plain")

    @server.route("/ping", [GET])
    def ping(req: Request):
        return Response(req, "pong", content_type="text/plain")

    @server.route("/config", [GET])
    def get_config(req: Request):
        raw = _read_json("/commands.json", {"buttons": []})
        btns = []
        for b in raw.get("buttons", []):
            b = dict(b)
            if "pin" in b and "pin_name" not in b:
                b["pin_name"] = str(b["pin"])
            btns.append(b)
        aes_key = _read_text("/aes.key").strip()
        return JSONResponse(req, {"buttons": btns, "aes_key": aes_key})

    @server.route("/config", [POST])
    def post_config(req: Request):
        try:
            data = req.json() or {}
            btns = _validate_buttons(data.get("buttons", []))

            # rotation sauvegarde
            try:
                if _exists("/commands.back"):
                    os.remove("/commands.back")
            except Exception:
                pass
            try:
                if _exists("/commands.json"):
                    os.rename("/commands.json", "/commands.back")
            except Exception:
                pass

            _write_json("/commands.json", {"buttons": btns})

            ak = (data.get("aes_key") or "").strip()
            if ak:
                ak = "".join(ch for ch in ak if ch.isalnum())[:24].ljust(24, "X")
                _write_text("/aes.key", ak)

            _ok(1)
            return JSONResponse(req, {"ok": True})
        except Exception as e:
            _ko(1)
            return JSONResponse(req, {"ok": False, "error": str(e)}, status=400)

    @server.route("/savekey", [POST])
    def savekey(req: Request):
        try:
            data = req.json() or {}
        except Exception:
            return JSONResponse(req, {"ok": False, "error": "Invalid JSON"}, status=400)

        aes_key   = (str(data.get("aes_key", "")).strip()
                     or _read_text("/aes.key").strip())
        key_name  = str(data.get("key_name", data.get("key name", ""))).strip()
        key_value = str(data.get("key_value", data.get("key value", "")))

        if not aes_key:
            return JSONResponse(req, {"ok": False, "error": "Missing aes_key"}, status=400)
        if not key_name:
            return JSONResponse(req, {"ok": False, "error": "Missing key_name"}, status=400)

        try:
            ensure_rw()
            manager = PasswordManager(aes_key)
            manager.store_password(key_name, key_value)
            _ok(1)
            return JSONResponse(req, {"ok": True, "key_name": key_name})
        except Exception as e:
            _ko(1)
            return JSONResponse(req, {"ok": False, "error": str(e)}, status=400)

    nonlocal_want_reload = [False]

    @server.route("/reboot", [GET, POST])
    def reboot(req: Request):
        try:
            ensure_rw()
            os.remove("/setup")  # désactive le mode setup au prochain boot
        except Exception as e:
            print(f"[SETUP] remove('/setup') failed: {e}")
        nonlocal_want_reload[0] = True
        return JSONResponse(req, {"ok": True})

    # ---------- Mappage STATIQUE sans wildcard ----------
    def _iter_files(base="/html", prefix=""):
        """Génère les chemins relatifs à /html pour tous les fichiers."""
        try:
            names = os.listdir(base)
        except OSError:
            return
        for name in names:
            if name.startswith("."):
                continue
            full = base + "/" + name
            rel = prefix + "/" + name if prefix else "/" + name
            try:
                st = os.stat(full)
            except OSError:
                continue
            # CircuitPython: pas de S_ISDIR portable, on teste via listdir
            is_dir = False
            try:
                _ = os.listdir(full)
                is_dir = True
            except OSError:
                is_dir = False
            if is_dir:
                # descente récursive
                for sub in _iter_files(full, rel):
                    yield sub
            else:
                yield rel  # ex: "/style.css", "/img/logo.png"

    def _register_static_routes():
        count = 0
        for rel_url in _iter_files("/html", ""):
            # on ignore /index.html (déjà route "/")
            if rel_url == "/index.html":
                continue
            # handler factory
            def make_handler(_rel):
                def handler(req: Request):
                    try:
                        return FileResponse(req, _rel)  # chemin relatif à /html
                    except OSError:
                        return Response(req, "Not found", status=404)
                return handler
            try:
                server.route(rel_url, [GET])(make_handler(rel_url))
                count += 1
            except Exception as e:
                print(f"[SETUP] route statique skip {rel_url}: {e}")
        # 404 propres pour requêtes courantes
        @server.route("/favicon.ico", [GET])
        def _fav(req: Request):
            return Response(req, "", status=404)
        @server.route("/apple-touch-icon.png", [GET])
        def _touch(req: Request):
            return Response(req, "", status=404)
        print(f"[SETUP] Routes statiques enregistrées: {count}")

    _register_static_routes()

    # ---------- Démarrage serveur ----------
    try:
        server.start(port=80)
        print("[SETUP] HTTP bind: 0.0.0.0:80")
    except Exception as e:
        print(f"[SETUP] start(port=80) failed: {e}")
        server.start(str(ip_ap))
        print(f"[SETUP] HTTP bind: {ip_ap}:80")

    print(f"[SETUP] HTTP: http://{ip_ap}/  (routes: /, /ping, /config [GET/POST], /savekey [POST], /reboot [GET/POST])")

    # ---------- Boucle poll ----------
    while True:
        try:
            server.poll()
        except OSError:
            # glitches AP transitoires
            pass
        except Exception as e:
            # logs utiles si un handler plante
            try:
                import traceback
                traceback.print_exception(e)
            except Exception:
                sys.print_exception(e)
            print(f"[SETUP] poll error type: {type(e).__name__} repr: {repr(e)}")
        if nonlocal_want_reload[0]:
            time.sleep(0.5)
            supervisor.reload()
        time.sleep(0.01)
