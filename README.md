# OPlus Toolkit

A GUI debloater for Oppo, OnePlus, and Realme devices running ColorOS, OxygenOS, or Realme UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)](#installation)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Safety Model](#safety-model)
- [Supported Devices](#supported-devices)
- [Installation](#installation)
- [Usage](#usage)
- [Debloat Levels](#debloat-levels)
- [FAQ](#faq)
- [Warnings](#warnings)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

OPlus Toolkit is an open-source desktop application that removes pre-installed bloatware from Oppo, OnePlus, and Realme devices. It uses ADB to uninstall or disable system apps at the user level, without requiring root access or unlocking the bootloader.

The tool is built around three principles:

- **Safe by Design**: packages known to cause bootloops or brick the device are blocked at the code level and cannot be selected in the GUI.
- **Transparency**: every operation displays the exact `adb shell` command that will run before execution.
- **Reversibility**: every real operation creates a timestamped backup that can be restored with one click.

No root. No custom ROM. No voided warranty. Only ADB, used properly.

---

## Features

| Area | Details |
|---|---|
| **Interface** | Material-inspired GUI built with CustomTkinter. Bilingual (English / Italian) with instant switching. Dark and light themes. |
| **Debloater** | Two curated lists (Light and Aggressive). Checkbox selection. Live search and filter in the All Packages view. Batch processing with progress bar. |
| **Actions** | Uninstall or disable packages. Restore removed packages from backup. |
| **Safety** | Hardcoded blacklist of 20+ dangerous packages. Command preview dialog before every real operation. Mandatory acknowledgement checkbox. Automatic timestamped backups. Dry-run mode. |
| **Detection** | Auto-detects device brand, model, Android version, and UI type (ColorOS, OxygenOS, Realme UI). |
| **Advanced** | Force mode (hidden, double confirmation) for power users. Complete audit log in `logs/`. |
| **Platform** | Linux, Windows, macOS. |

---

## Safety Model

Removing the wrong system package can cause a bootloop, disable essential features (calls, WiFi, NFC, Bluetooth), or in the worst case require a factory reset.

OPlus Toolkit mitigates these risks with four layers of protection:

### 1. Hardcoded Blacklist

Packages such as `com.oplus.appplatform`, `com.coloros.bootreg`, `com.android.systemui`, and `com.coloros.safecenter` are permanently blocked. The GUI does not allow selecting them, and `core.py` refuses to process them even if called directly from code.

### 2. Command Preview

Before any real operation, a dialog shows the exact commands to be executed. Example:

```
adb shell pm uninstall --user 0 com.android.email
adb shell pm uninstall --user 0 com.heytap.music
```

The user must read the warning banner and tick a checkbox to enable the Execute button.

### 3. Automatic Backups

Every real operation (non-dry-run) writes a timestamped JSON file to `backups/`:

```
backups/backup_20260922_154230.json
```

Backups can be restored from the Backups tab with a single click.

### 4. Dry-Run Mode

Dry-run is enabled by default. In this mode, the app simulates every operation and shows exactly what would happen, without touching the device.

**Recommended workflow:** always run a new batch in dry-run mode first. Read the commands. Then execute for real.

---

## Supported Devices

| UI | Brand | Android Versions | Status |
|---|---|---|---|
| ColorOS | Oppo, OnePlus (China) | 11 – 16 | Full support |
| OxygenOS | OnePlus (Global) | 11 – 16 | Full support |
| Realme UI | Realme | 2.0 – 7.0 | Full support |

The toolkit auto-detects the UI type and version, and adapts the curated lists accordingly.

---

## Installation

### Requirements

- Python 3.11 or newer
- ADB (Android Platform Tools) in your `PATH`
- Git (only for the clone method)
- USB cable that supports data transfer
- USB debugging enabled on your phone

### Linux

```bash
# Debian / Ubuntu
sudo apt install python3 python3-venv python3-tk android-tools-adb git

# Arch / CachyOS / Manjaro
sudo pacman -S python tk android-tools git

# Clone the repository
git clone https://github.com/mrcbr33/oplus-toolkit.git
cd oplus-toolkit

# Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate          # bash / zsh
# source .venv/bin/activate.fish   # fish

# Install Python dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

### Windows

```powershell
# Install Python 3.11+ from python.org (check "Add Python to PATH")
# Install Android Platform Tools and add them to PATH

git clone https://github.com/mrcbr33/oplus-toolkit.git
cd oplus-toolkit

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

### macOS

```bash
brew install python@3.11 android-platform-tools git

git clone https://github.com/mrcbr33/oplus-toolkit.git
cd oplus-toolkit

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## Usage

### Step 1 — Enable USB debugging on your phone

1. Open **Settings → About device**.
2. Tap **Build number** seven times to enable Developer Options.
3. Go to **Settings → System → Developer Options**.
4. Enable **USB debugging**.
5. Optionally enable **Stay awake**.

### Step 2 — Connect your phone

1. Connect the phone to the computer with a data-capable USB cable.
2. On the phone, accept the prompt **"Allow USB debugging?"**.
3. Tick **"Always allow from this computer"**.

Verify the connection:

```bash
adb devices
```

Expected output:

```
List of devices attached
A1B2C3D4E5    device
```

If you see `unauthorized`, re-accept the popup. If you see `offline`, run `adb kill-server && adb start-server`.

### Step 3 — Launch the toolkit

```bash
python app.py
```

### Step 4 — Navigate the sections

| Section | Description |
|---|---|
| **Dashboard** | Shows device info: brand, model, Android version, UI type and version. Buttons to refresh info and restart the ADB server. |
| **Debloater** | The main screen. Choose a level (Light or Aggressive), pick an action (Uninstall or Disable), select packages, and run. Dry-run is on by default. |
| **All Packages** | Full list of every installed and disabled package on the device. Search and filter by state. Curated and blacklisted packages are tagged. Force mode unlocks the rest. |
| **Backups** | Lists every backup file created. One click to restore. |
| **Settings** | Switch language (EN/IT), theme (Dark/Light), and enable Force mode (with double confirmation). |

### Step 5 — First debloat

1. Go to **Debloater**.
2. Leave **Dry run** enabled.
3. Select 2–3 safe packages (e.g. `com.android.email`, `com.heytap.music`).
4. Click **Run**.
5. Read the command preview and tick the acknowledgement checkbox.
6. Click **Execute**.
7. Verify that the results dialog shows all green.

Now you are ready for a real run: same process, with **Dry run disabled**.

---

## Debloat Levels

The curated lists are organized into three safety tiers.

| Tier | Name | Description |
|---|---|---|
| 🟢 | **Light** | Packages that are universally safe to remove on any OPlus device. Redundant apps, duplicated services, unused Heytap utilities. Recommended for most users. |
| 🟡 | **Aggressive** | Advanced removal. Some packages may disable specific features (AI, theming, gaming overlays, cloud sync). Read each description before selecting. For power users only. |
| 🔴 | **Blacklist** | Never remove. These 20+ packages cause bootloops, bricked devices, or loss of core functionality. The toolkit blocks them at the code level. They are shown in the All Packages view, tagged as `BLACKLIST`. |

Each entry in the curated lists has three fields:

```json
{
  "package": "com.heytap.music",
  "name": "HeyTap Music",
  "reason": "Redundant media player."
}
```

- `package` — Android package ID (used by ADB)
- `name` — human-readable name
- `reason` — why it is safe to remove

---

## FAQ

**Do I need root?**
No. OPlus Toolkit uses `adb shell pm uninstall --user 0`, which removes the app for the current user without touching the system partition. This is reversible with `adb shell cmd package install-existing`.

**Will this void my warranty?**
No. You are not unlocking the bootloader, flashing anything, or modifying system partitions. Everything is done at the user level via ADB.

**Can I get an app back after removing it?**
Yes. Two ways:
1. From a backup: go to the Backups tab, find the relevant file, click Restore.
2. Manually: `adb shell cmd package install-existing com.example.app`.

**What is Force Mode?**
Force mode unlocks the ability to select packages outside the curated lists in the All Packages view. It is dangerous and hidden in Settings behind two consecutive confirmation dialogs. Even with force mode enabled, blacklisted packages remain blocked. Only enable it if you know exactly what you are doing.

**Does it work on non-OPlus phones?**
Technically yes, the ADB core is generic. But the curated lists are specific to ColorOS, OxygenOS, and Realme UI. On a Samsung, Pixel, or Xiaomi device, different lists would be required.

**Where are logs and backups stored?**
- Logs: `logs/oplus_toolkit_YYYYMMDD.log`
- Backups: `backups/backup_YYYYMMDD_HHMMSS.json`
- Config: `config.json`

All three are excluded from Git via `.gitignore`.

**Why is my device not detected?**
Checklist:
1. Is the cable data-capable? Try a different cable.
2. Did you accept the "Allow USB debugging" prompt on the phone?
3. Does `adb devices` show it?
4. Try Dashboard → Restart ADB server.
5. On Windows, you may need the Oppo/OnePlus USB drivers.

---

## Warnings

- **Never** remove packages outside the curated lists unless you fully understand the consequences.
- **Never** disable Force mode's safety rails "just to see what happens".
- **Never** skip the command preview.
- **Always** run new batches in dry-run mode first.
- **Always** verify that the backup appeared in the Backups tab before continuing.
- **Always** keep important data backed up off the phone.

The developer is not responsible for any damage caused to your device. Use at your own risk.

---

## Contributing

Contributions are welcome.

- **Report bugs** — open an issue with your device model, UI version, and the exact error.
- **Suggest packages** — found a bloatware package missing from the lists? Open an issue with the package ID and your device.
- **Improve the UI** — themes, icons, layout, translations.
- **Improve the docs** — fix typos, add examples, translate to more languages.
- **Test on new devices** — ColorOS 16, OxygenOS 16, Realme UI 7.0.

### Pull request workflow

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/oplus-toolkit.git
cd oplus-toolkit

# 3. Create a feature branch
git checkout -b feature/my-feature

# 4. Make your changes and commit
git commit -m "Add my feature"

# 5. Push and open a Pull Request
git push origin feature/my-feature
```

---

## License

Released under the MIT License. See [LICENSE](LICENSE) for the full text.

---

## Acknowledgements

This project exists because of the open-source community and the work of debloating enthusiasts on XDA Developers, GitHub, and countless forum threads. Thanks to the maintainers of Android Platform Tools and CustomTkinter.
