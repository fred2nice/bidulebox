# BiduleBox

<img width="3000" height="2000" alt="bidule" src="https://github.com/user-attachments/assets/a8f3a49c-0264-4960-b8fb-9ab7d8a01ecc" />



> **Macro keyboard for Raspberry Pi Pico W — Wi-Fi only for setup, USB HID for daily use.**

**Why “Bidule”?**  
_en français_, **bidule** veut dire *truc/machin/thingamajig* — le truc dont on ne sait pas trop quoi faire, jusqu’au moment où on en a besoin. BiduleBox se transforme en un **pupitre de macros** propre, configurable et sûr.

---

## Overview

BiduleBox is a **Raspberry Pi Pico W** macro keyboard. It spins up a **Wi-Fi AP only in setup mode** to serve a tiny web UI, then runs as a **pure USB HID keyboard** in normal use. Map buttons to commands/macros and **store secrets encrypted (AES)** from a physical button-sequence–derived key.

Why make a Bidule for keyboard macros when that already exists? Because I didn’t want plaintext passwords or passphrases sitting inside macros.

It’s also a way to try CircuitPython and do a bit of electronics—a project to test and learn. It is not ready to use, and should only be used by people who know what they’re doing.

For example, you can assign a button to launch PuTTY, log in as “user,” type the password, run sudo and execute a command; or connect to a first server, start a VPN, and SSH into another.

Decryption happens at every BiduleBox startup. The key is a 24-character AES key generated from a sequence of button presses, so it’s not easy to guess and is reasonably hard to crack. However, if the key is known/entered, it’s easy to recover the passwords in plaintext.

Again, this isn’t production-ready code. It’s good enough for me, and if it gives you ideas or helps, great. 😊


### Features

- USB HID macro keyboard (Windows **FR** layout by default).
- **Wi-Fi AP only for setup** → no Wi-Fi in normal mode.
- Need to create a file setup to enable AP Mode
- Web UI to edit button mapping and timings.
- Secret storage via `PasswordManager(aes_key)` (24-char key derived from button sequence).
- Safe config rollback: `commands.json` → `commands.back` then write new file.
- Visual reboot flow + minimal HUD UI.

- Web UI ScreenShot

<img width="2101" height="1663" alt="image" src="https://github.com/user-attachments/assets/5911854e-426a-4fe2-a4f1-493199cdc13d" />

<img width="1812" height="1219" alt="image" src="https://github.com/user-attachments/assets/681540c5-0f45-4391-ad91-0a0c2601f0d2" />

---

## Quick start

1. **Flash CircuitPython** on a Raspberry Pi **Pico W**.  
2. **Copy files** to the `CIRCUITPY` drive:
3. Create a file setup ( no extension )
4. Reboot
5. Connect BiduleBox SSID
<img width="277" height="102" alt="image" src="https://github.com/user-attachments/assets/a85374e5-a6f5-4cda-b1e1-be86403a6ade" />
<img width="639" height="356" alt="image" src="https://github.com/user-attachments/assets/c51acb70-cc39-4a6e-be6e-5cc27dbc14a2" />
6. Go to http://192.168.4.1 or other IP Address
7. Create a key ( key name text only ), push buttons to have 24/24 AES Key then click on Done
8. Assign macro or command to buttons
9. Reboot ( click on the switch )
10. Unplug / Plug

Commands and buttons dfintion are stored inside /commands.json macros inside macros/name.json to use macro with button => use macro_FILENAME

Et voilà !


