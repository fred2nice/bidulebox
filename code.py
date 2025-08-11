import board
import digitalio
import pwmio
import time
import usb_hid
import json
import os
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_win_fr import KeyboardLayout  # Layout FR

# BLE importé mais non utilisé en mode normal ; conservé si besoin futur
import adafruit_ble
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_ble.services.standard.device_info import DeviceInfoService

from password_manager import PasswordManager
#3 → 2 → 1 → 3 → 2 → 1 → 3 → 2 → 1 → 3 → 2 → 1 → 5 → 2 → 3

# -------------------- Helpers setup / fichiers --------------------
def setup_mode():
    try:
        os.stat("/setup")
        return True
    except OSError:
        return False


def _pin_from_name(name: str):
    # Attend "GPxx"
    try:
        return getattr(board, name)
    except AttributeError:
        raise ValueError(f"Pin inconnu: {name}")


def load_buttons_from_json(path="/commands.json"):
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Impossible de lire {path}: {e}")
        return []

    btns = []
    seen_ids = set()
    for entry in data.get("buttons", []):
        try:
            bid = int(entry["id"])
            if bid in seen_ids:
                print(f"[WARN] id {bid} dupliqué: ignoré")
                continue
            seen_ids.add(bid)
            pin = _pin_from_name(entry["pin"])
            color = entry.get("color", "")
            macro = entry.get("macro", "")
            cmd = entry.get("command", "")
            pass_key = entry.get("pass_key", "")
            winsearch = bool(entry.get("winsearch", True))
            delay_ms = int(entry.get("delay_ms", 500))

            btns.append({
                "id": bid,
                "couleur": color,
                "pin": pin,
                "macro": macro,          # ex: "demeter"
                "command": cmd,          # fallback direct si macro vide
                "pass_key": pass_key,
                "winsearch": winsearch,
                "delay_ms": delay_ms
            })
        except Exception as e:
            print(f"[WARN] bouton ignoré (entrée invalide): {entry} ; err={e}")
            continue
    return btns


# -------------------- LEDs feedback --------------------
def blink_ok(n: int):
    """Clignote la LED verte n fois (0,2s ON / 0,2s OFF)."""
    for _ in range(n):
        led.value = True
        time.sleep(0.2)
        led.value = False
        time.sleep(0.2)


def blink_ko(n: int):
    """Clignote la LED rouge n fois (0,2s ON / 0,2s OFF)."""
    for _ in range(n):
        led_red.value = True
        time.sleep(0.2)
        led_red.value = False
        time.sleep(0.2)


# -------------------- Macros "musique" (exemple hors JSON) --------------------
def macro_marche():
    # Define the notes (in Hz) and corresponding durations (in seconds)
    NOTES = [
        (392, 0.5),  # G
        (392, 0.5),  # G
        (392, 0.5),  # G
        (311, 0.35), # Eb
        (466, 0.15), # Bb
        (392, 0.5),  # G
        (311, 0.35), # Eb
        (466, 0.15), # Bb
        (392, 1.0),  # G
        (587, 0.5),  # D
        (587, 0.5),  # D
        (587, 0.5),  # D
        (622, 0.35), # Eb (octave above)
        (466, 0.15), # Bb
        (370, 0.5),  # F#
        (311, 0.35), # Eb
        (466, 0.15), # Bb
        (392, 1.0),  # G
    ]
    buzzer = pwmio.PWMOut(board.GP20, variable_frequency=True)
    for frequency, duration in NOTES:
        buzzer.frequency = frequency
        buzzer.duty_cycle = 2**15
        time.sleep(duration)
        buzzer.duty_cycle = 0
        time.sleep(0.05)
    buzzer.deinit()


# -------------------- USB HID --------------------
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayout(keyboard)

# LED carte
led_board = digitalio.DigitalInOut(board.LED)
led_board.direction = digitalio.Direction.OUTPUT

# Switch ON/OFF (pull-up)
switch = digitalio.DigitalInOut(board.GP15)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# Charge config boutons
buttons_config = load_buttons_from_json()

# Instancie les entrées physiques
buttons = []
for config in buttons_config:
    button = digitalio.DigitalInOut(config["pin"])
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    buttons.append((
        button,
        config["id"],
        config["couleur"],
        config["macro"],
        config["command"],
        config["pass_key"],
        config.get("winsearch", True),
        config.get("delay_ms", 500)
    ))

# Comptage appuis (mode OFF → construction aes_key)
button_press_counts = {config["id"]: 0 for config in buttons_config}
button_press_order = []
previous_switch_state = switch.value
display_message = True
transition_message_displayed = False


# -------------------- ENVOI d'une seule action --------------------
def send_command(winsearch, command, password_key=None, delay_ms=1000):
    global aes_key
    led.value = True
    print(f"Delay : {delay_ms} ms") 

    if winsearch:
        keyboard.press(Keycode.WINDOWS, Keycode.R)
        keyboard.release_all()
        
        time.sleep(max(0, delay_ms)/1000)
        

    keyboard_layout.write(command)
    time.sleep(0.2)
    led.value = False

    if password_key:
        led.value = True
        print(f"Longueur de la clé AES : {len(aes_key)} octets")
        if len(aes_key) == 24:
            try:
                manager = PasswordManager(aes_key)
                password = manager.load_password(password_key) + '\n'
                blink_ok(3)
            except Exception as e:
                password = ""
                blink_ko(3)
                print(f"[ERR] PasswordManager.load_password: {e}")
        else:
            password = ""
            led.value = False
            led_red.value = True

        time.sleep(2)  # laisser l'appli se connecter
        keyboard_layout.write(password)
        time.sleep(0.5)
        led.value = False

def run_action(a):
    """Exécute UNE action normalisée (texte OU combo de touches)."""
    # Priorité aux combos de touches si présents
    if a.get("keys"):
        kcs = _keycodes_from_names(a["keys"])
        if kcs:
            keyboard.send(*kcs)  # press + release
        else:
            print("[MACROS] aucune touche valide dans 'keys'")
    else:
        # Action "texte" classique
        send_command(
            a.get("winsearch", False),
            a.get("command", "") or "",
            (a.get("password_key") or None),
            a.get("delay_ms", 0)
        )

    # Pause optionnelle de fin d’action
    sm = int(a.get("sleep_ms", 0))
    if sm > 0:
        time.sleep(sm / 1000)


# -------------------- Système de MACROS JSON --------------------
# Structure acceptée dans macros/<name>.json :
# {
#   "actions": [
#     { "winsearch": true/false, "delay_ms": int, "command": "str", "password_key": "str", "sleep_ms": int },
#     ...
#   ]
# }

def _norm_action(a):
    """Normalise une action JSON en dict complet (texte OU combo de touches)."""
    try:
        # keys peut être une liste ["CTRL","D"] ou une string "CTRL+D"
        raw_keys = a.get("keys")
        if isinstance(raw_keys, str):
            keys = [s.strip() for s in raw_keys.split("+") if s.strip()]
        elif isinstance(raw_keys, list):
            keys = [str(x).strip() for x in raw_keys if str(x).strip()]
        else:
            keys = []

        return {
            "winsearch": bool(a.get("winsearch", False)),
            "delay_ms": int(a.get("delay_ms", 0)),
            "command": str(a.get("command", "")),
            "password_key": str(a.get("password_key", "")),
            "sleep_ms": int(a.get("sleep_ms", 0)),
            "keys": keys,
        }
    except Exception as e:
        print(f"[MACROS] action invalide: {a} ; err={e}")
        return None

def _keycodes_from_names(names):
    """Convertit une liste de noms ['CTRL','D','ENTER'] en Keycodes."""
    out = []
    for n in (names or []):
        u = n.upper()
        if u in ("CTRL", "CONTROL", "LEFT_CTRL", "LCTRL"): out.append(Keycode.CONTROL)
        elif u in ("ALT", "LEFT_ALT", "LALT"):             out.append(Keycode.ALT)
        elif u in ("SHIFT", "LEFT_SHIFT", "LSHIFT"):       out.append(Keycode.SHIFT)
        elif u in ("WIN", "WINDOWS", "GUI"):               out.append(Keycode.WINDOWS)
        elif u in ("ENTER", "RETURN"):                     out.append(Keycode.ENTER)
        elif u in ("TAB",):                                out.append(Keycode.TAB)
        elif u in ("ESC", "ESCAPE"):                       out.append(Keycode.ESCAPE)
        elif u in ("SPACE", "SPACEBAR"):                   out.append(Keycode.SPACE)
        elif u in ("BKSP", "BACKSPACE"):                   out.append(Keycode.BACKSPACE)
        elif u in ("UP", "ARROW_UP"):                      out.append(Keycode.UP_ARROW)
        elif u in ("DOWN", "ARROW_DOWN"):                  out.append(Keycode.DOWN_ARROW)
        elif u in ("LEFT", "ARROW_LEFT"):                  out.append(Keycode.LEFT_ARROW)
        elif u in ("RIGHT", "ARROW_RIGHT"):                out.append(Keycode.RIGHT_ARROW)
        elif len(u) == 1 and "A" <= u <= "Z":              out.append(getattr(Keycode, u))
        else:
            print(f"[KEYS] Ignoré: '{n}' (non mappé)")
    return out


def load_macros_from_dir(base="/macros"):
    """Charge toutes les macros JSON en mémoire: {name: [actions...]}"""
    macros = {}
    try:
        files = os.listdir(base)
    except OSError:
        print(f"[MACROS] dossier absent: {base}")
        return {}

    for fn in files:
        if not fn.endswith(".json"):
            continue
        name = fn[:-5]  # sans .json
        path = base + "/" + fn
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[MACROS] lecture échouée {path}: {e}")
            continue

        actions = data.get("actions")
        # tolérance: certains pourraient écrire "action" (singulier)
        if actions is None and "action" in data:
            actions = data["action"]
        if isinstance(actions, dict):
            actions = [actions]
        if not isinstance(actions, list):
            print(f"[MACROS] format invalide dans {path} (attendu 'actions' liste)")
            continue

        norm = []
        for a in actions:
            if not isinstance(a, dict):
                continue
            na = _norm_action(a)
            if na is not None:
                norm.append(na)

        macros[name] = norm
        print(f"[MACROS] chargé {name} ({len(norm)} action(s))")
    print(f"[MACROS] total: {len(macros)} macro(s)")
    return macros


MACROS = load_macros_from_dir("/macros")

def run_macro(name: str) -> bool:
    """Exécute macro par nom : fichier JSON prioritaire, sinon fonction macro_<name>."""
    name = (name or "").strip()
    if not name:
        return False

    if name in MACROS:
        actions = MACROS[name]
        print(f"[MACROS] exec fichier '{name}' ({len(actions)} action(s))")
        for idx, a in enumerate(actions, start=1):
            try:
                run_action(a)
            except Exception as e:
                print(f"[MACROS] action #{idx} échouée: {e}")
                blink_ko(1)
                return False           # <-- erreur ⇒ False
        return True                     # <-- succès ⇒ True

    func_name = f"macro_{name}"
    if func_name in globals():
        print(f"[MACROS] exec fonction {func_name}()")
        try:
            globals()[func_name]()
            return True
        except Exception as e:
            print(f"[MACROS] erreur dans {func_name}: {e}")
            blink_ko(2)
            return False

    print(f"[MACROS] inconnue: '{name}' (pas de fichier JSON ni de fonction)")
    return False



# -------------------- (Exemples de macros fonctionnelles en fallback) --------------------
def macro_example():
    send_command(True, "https://www.fillon.org\n", "",1000)
    time.sleep(2)
    





# -------------------- GPIO annexes & LEDs couleurs --------------------
# Faux GND GP16
faux_gnd = digitalio.DigitalInOut(board.GP16)
faux_gnd.direction = digitalio.Direction.OUTPUT
faux_gnd.value = False

# LED verte
led = digitalio.DigitalInOut(board.GP17)
led.direction = digitalio.Direction.OUTPUT

# Faux GND GP8
faux_gnd2 = digitalio.DigitalInOut(board.GP8)
faux_gnd2.direction = digitalio.Direction.OUTPUT
faux_gnd2.value = False

# LED rouge
led_red = digitalio.DigitalInOut(board.GP9)
led_red.direction = digitalio.Direction.OUTPUT


# -------------------- Mode setup (Wi-Fi/HTTP) --------------------
if setup_mode():
    import setup
    setup.run(blink_ok=blink_ok, blink_ko=blink_ko, led=led, led_red=led_red)


# -------------------- Boot feedback --------------------
blink_ko(3)
blink_ok(3)

aes_key = ''


# -------------------- Boucle principale --------------------
i = 0
while True:
    current_switch_state = switch.value
    led.value = False
    led_red.value = False

    if current_switch_state:  # Switch OFF (valeur HIGH) → capture AES key
        if display_message:
            print("Switch à OFF :")
            print("Presser les boutons.")
            display_message = False

        for button, id, couleur, macro, command, pass_key, winsearch, delay_ms in buttons:
            if not button.value:  # appui
                button_press_counts[id] += 1
                button_press_order.append(id)
                led.value = True
                print(f"Bouton pressé : ID {id}")

                # Construction de la chaîne AES 24
                button_sequence_str = ''.join(str(i) for i in button_press_order)
                button_press_counts_str = ''.join(
                    f"{i}{button_press_counts[i]}"
                    for i in sorted(button_press_counts) if button_press_counts[i] > 0
                )
                final_str = f"{button_sequence_str}X{button_press_counts_str}"
                print(final_str)
                print(f"Longueur de la chaîne : {len(final_str)}")

                if len(final_str) == 24:
                    aes_key = final_str
                    blink_ok(10)

                time.sleep(0.3)  # anti-rebond

    else:  # Switch ON (valeur LOW) → fonctionnement normal
        if i % 10 == 0:
            led_red.value = True
        i += 1

        if not previous_switch_state:  # OFF -> ON
            if not transition_message_displayed:
                print("Passage de OFF à ON")
                print("Liste des boutons pressés dans l'ordre :")
                for id in button_press_order:
                    couleur = next(config["couleur"] for config in buttons_config if config["id"] == id)
                    print(f"Bouton {couleur} (ID: {id})")
                # Reset
                button_press_counts = {config["id"]: 0 for config in buttons_config}
                button_press_order = []
                transition_message_displayed = True
                try:
                    manager = PasswordManager(aes_key)
                    _ = manager.load_password('rpi') + '\n'
                    blink_ok(2)
                except Exception as e:
                    print(f"[AES] test clé: {e}")
                    blink_ko(6)

        # Exécution des boutons
        for button, id, couleur, macro, command, pass_key, winsearch, delay_ms in buttons:
            if not button.value:
                if macro:
                    ok = run_macro(macro)
                    if not ok:
                        blink_ko(2)
                else:
                    send_command(winsearch, command, pass_key, delay_ms)
                time.sleep(0.5)  # anti-rebond

    # Transition de switch
    if previous_switch_state != current_switch_state:
        previous_switch_state = current_switch_state
        if current_switch_state:  # ON -> OFF
            display_message = True
            transition_message_displayed = False

    led_red.value = False
    time.sleep(0.1)
