# BiduleBox

[![GitHub release](https://img.shields.io/github/v/release/fred2nice/BiduleBox?label=Release&color=blue)](https://github.com/fred2nice/BiduleBox/releases)  
[![License](https://img.shields.io/github/license/fred2nice/BiduleBox?color=green)](LICENSE)  
[![Issues](https://img.shields.io/github/issues/fred2nice/BiduleBox?color=orange)](https://github.com/fred2nice/BiduleBox/issues)  
[![Last Commit](https://img.shields.io/github/last-commit/fred2nice/BiduleBox?color=purple)](https://github.com/fred2nice/BiduleBox/commits/main)  

<img width="3000" height="2000" alt="bidule" src="https://github.com/user-attachments/assets/a8f3a49c-0264-4960-b8fb-9ab7d8a01ecc" />

> **Macro keyboard for Raspberry Pi Pico W — Wi-Fi only for setup, USB HID for daily use.**

---

## 📖 Why “Bidule”?

En français, **bidule** veut dire *truc/machin/thingamajig* — l’objet dont on ne sait pas trop quoi faire, jusqu’au moment où on en a besoin.  
BiduleBox se transforme en un **pupitre de macros** propre, configurable et sécurisé.

---

## 🔍 Overview

BiduleBox is a **Raspberry Pi Pico W** macro keyboard. It starts a **Wi-Fi AP only in setup mode** to serve a tiny web UI, then runs as a **pure USB HID keyboard** in normal use.  
You can map buttons to commands/macros and **store secrets encrypted (AES)** using a key derived from a physical button sequence.

Why another macro keyboard? Because I didn’t want plaintext passwords or passphrases sitting inside macros.

It’s also a way to experiment with CircuitPython and electronics — a test-and-learn project.  
⚠️ **Not production-ready** — for advanced users only.

**Example usage:**  
Assign a button to launch PuTTY, log in, run `sudo`, execute a command, or even connect to a first server, start a VPN, and SSH into another.

**Security note:**  
Decryption happens at every BiduleBox startup. The key is a 24-character AES key generated from a sequence of button presses. Key cannot be recovered.

---

## ✨ Features

- USB HID macro keyboard (Windows **FR** layout by default)
- **Wi-Fi AP only for setup** → no Wi-Fi in normal mode
- Setup mode enabled by creating a `setup` file (no extension)
- Web UI to edit button mapping and timings
- Secret storage via `PasswordManager(aes_key)` (24-char key derived from button sequence)
- Safe config rollback: `commands.json` → `commands.back`
- Minimal HUD and reboot UI

---

## 🖼 Web UI Screenshots

<img width="2101" height="1663" alt="image" src="https://github.com/user-attachments/assets/5911854e-426a-4fe2-a4f1-493199cdc13d" />

<img width="1812" height="1219" alt="image" src="https://github.com/user-attachments/assets/681540c5-0f45-4391-ad91-0a0c2601f0d2" />

---

## 🚀 Quick start

1. **Flash CircuitPython** on a Raspberry Pi **Pico W**  
2. **Copy files** to the `CIRCUITPY` drive  
3. Create a file named `setup` (no extension)  
4. Reboot the device  
5. Connect to the `BiduleBox` SSID  

   <img width="277" height="102" alt="image" src="https://github.com/user-attachments/assets/a85374e5-a6f5-4cda-b1e1-be86403a6ade" />  
   <img width="639" height="356" alt="image" src="https://github.com/user-attachments/assets/c51acb70-cc39-4a6e-be6e-5cc27dbc14a2" />

6. Open [http://192.168.4.1](http://192.168.4.1) (or the displayed IP)  
7. Create a key:  
   - Enter a key name (text only)  
   - Press buttons until you reach 24/24 for the AES key  
   - Click **Done**  
8. Assign macros or commands to buttons  
9. Reboot (click the switch)  
10. Unplug / Plug back the device

**File storage:**  
- Commands and button definitions: `/commands.json`  
- Macros: `/macros/name.json`  
- To assign a macro to a button, use `macro_FILENAME` as the command.

Et voilà 🎉
