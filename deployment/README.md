# Raspberry Pi Zero W deployment (Step 7)

This guide prepares the existing VIHAAN application for the **original
Raspberry Pi Zero W (512 MB, ARMv6)**. It does not configure or test GPIO/I2S.
The 40-pin header is unsoldered, so use `HARDWARE_MODE=simulation` for the
initial SSH-only run. Never select `auto` on this board until the hardware is
connected and the manual hardware checks below have been completed.

## OS, architecture, and package compatibility

The official Raspberry Pi OS documentation currently recommends Raspberry Pi
OS Lite for headless and older boards such as the original Pi Zero, and its
32-bit edition for 32-bit processors. The current published Raspberry Pi OS
Lite `armhf` image index includes an image dated 2026-10-06; the OS documentation
identifies Debian Trixie as the latest major release. Use Raspberry Pi Imager
and select the newest **Raspberry Pi OS Lite (32-bit)** image that Imager
offers for the original Zero W. Do not select a 64-bit image.

The board and its installed OS have not been inspected from this development
workspace. Before installing packages, SSH to the Pi and record:

```sh
printf 'Model: '
tr -d '\000' </proc/device-tree/model
printf '\nArchitecture: '
uname -m
printf 'Word size: '
getconf LONG_BIT
printf 'Debian architecture: '
dpkg --print-architecture
cat /etc/os-release
python3 --version
python3 -c 'import platform, struct; print(platform.machine(), struct.calcsize("P") * 8)'
```

For the original Zero W, expect the model to identify Zero W, `armv6l`, 32-bit
and Raspberry Pi OS's `armhf` architecture. The installed Python version is
not known until this is run. Current Groq Python SDK releases require Python
3.10 or later; stop and resolve the OS/Python mismatch before installing if
`python3` is older.

Dependency notes for ARMv6:

| Dependency | Use and deployment note |
|---|---|
| `groq` | Pure-Python SDK, but depends on Pydantic. Current SDK metadata requires Python 3.10+ and allows Pydantic below version 3. |
| `pydantic-core` | Pydantic 2's native Rust extension. Current PyPI wheels include ARMv7 and AArch64, not ARMv6. Do not assume a source build will succeed within 512 MB. |
| `pydantic<2` | The Pi simulation requirements constrain Groq to the SDK's Pydantic-v1 compatibility path, avoiding `pydantic-core`. Pydantic may still need a native/source build; validate on the Pi. |
| `python-dotenv` | Pure Python configuration loader; no device access. |
| `PyAudio` / PortAudio | Not installed for software-only simulation. The PyPI release provides a source distribution and Windows wheels, not a verified ARMv6 wheel. Install/test only after I2S hardware is assembled. |
| `RPi.GPIO` | Imported lazily by `PiButton`; omitted from the simulation profile. Check the target OS's compatible package and venv visibility before enabling real GPIO. |
| `pytest` | Test-only. It is included in the Pi simulation profile, not needed for normal service operation. |
| `requests` | Used only by the optional generic HTTP helper, not by Groq; omitted from the Pi simulation profile. |
| `espeak-ng` | Native OS executable, installed using APT; no Python TTS package is used. |

The profile in `requirements-pi-simulation.txt` plus
`armv6-constraints.txt` is a cautious installation attempt, not a claim that
PyPI dependencies have been built or tested on this board. If Pydantic cannot
be installed, do not try to build the latest Rust `pydantic-core` on the Pi.
Check whether the current OS repository provides compatible `python3-pydantic`
and `python3-pydantic-core` packages (`apt-cache policy ...`) and validate
using an isolated, target-compatible environment. Do not proceed to service or
hardware activation until the import smoke test and tests pass.

Official references:

- [Raspberry Pi OS editions and architecture](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/os/rpi-os-introduction.adoc)
- [Raspberry Pi Python and virtual environments](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/os/using-python.adoc)
- [Current 32-bit Lite image index](https://downloads.raspberrypi.com/raspios_lite_armhf/images/)
- [Groq SDK package metadata](https://pypi.org/project/groq/)
- [Pydantic Core package files](https://pypi.org/project/pydantic-core/)
- [PyAudio package files and Linux installation notes](https://pypi.org/project/PyAudio/)

## Prepare Raspberry Pi OS and SSH

1. Back up the SD card; writing an image erases it.
2. In Raspberry Pi Imager, choose the current Raspberry Pi OS Lite **32-bit**
   image. Set a unique hostname, create a non-default user and password, set
   the correct WLAN country, configure Wi-Fi, and enable SSH with public-key
   authentication where possible.
3. Boot the Pi on a stable power supply. Find its address from the router or
   use its configured mDNS name, then connect:

   ```sh
   ssh <username>@<hostname>.local
   ```

4. Run the pre-install checks above. Do not continue if model or architecture
   does not match the original Zero W.
5. Update the OS:

   ```sh
   sudo apt update
   sudo apt full-upgrade -y
   sudo reboot
   ```

6. Reconnect over SSH and install only the software-mode prerequisites:

   ```sh
   sudo apt install -y git python3 python3-venv python3-pip \
       ca-certificates curl espeak-ng
   ```

   `build-essential` and `python3-dev` may be required if pip must build
   Pydantic from source. Install them only if the dependency installation
   reports that need; a build on a 512 MB Pi may be slow or run out of memory.

## Wi-Fi setup

Prefer Raspberry Pi Imager's first-boot Wi-Fi configuration. Raspberry Pi OS
Lite uses the OS network manager; VIHAAN does not create networks, change Wi-Fi
settings, or store Wi-Fi passwords.

- **Normal 2.4 GHz network:** select the SSID and enter its passphrase in
  Imager, or configure it interactively through Raspberry Pi OS. Ensure the
  router's 2.4 GHz network is enabled and set the correct WLAN country.
- **OnePlus 9 Pro hotspot:** enable the phone's hotspot and choose its 2.4 GHz
  compatibility/band option. Configure its SSID/passphrase through Imager or
  the OS network settings. Hotspot menu names vary by OxygenOS version.

Do not put the Wi-Fi passphrase in source, shell commands, or logs. Verify
association and internet independently:

```sh
iwgetid -r
nmcli device status
curl -I --max-time 5 https://api.groq.com
```

`iwgetid` may not be installed; `nmcli` availability and interface names vary
by OS release. A connected Wi-Fi interface does not guarantee internet access.
Check DHCP, DNS, captive portals, time synchronization, and outbound HTTPS if
the Groq endpoint cannot be reached.

## Install and configure software-only simulation

Use the SSH user's home directory for the first manual trial; this avoids
changing system files or needing root for application execution:

```sh
git clone https://github.com/tanveersingh0902/AI_PIN.git ~/AI_PIN
cd ~/AI_PIN
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install \
    -c deployment/armv6-constraints.txt \
    -r deployment/requirements-pi-simulation.txt
python -m pip check
python -c 'from importlib.metadata import version; import groq, pydantic; print("Groq", version("groq"), "Pydantic", pydantic.__version__)'
```

If dependency installation fails or attempts an unsupported native build, stop
and record the complete error. Do not silently drop Groq or substitute another
provider/model.

Create a private configuration file without overwriting an existing one:

```sh
test ! -e .env && cp .env.example .env
chmod 600 .env
nano .env
```

Set `GROQ_API_KEY` to the real key in the editor and set:

```ini
HARDWARE_MODE=simulation
```

The example key is only a placeholder. `.env` is excluded by `.gitignore`.
The same configured `GROQ_API_KEY` is passed to the existing Whisper and LLM
clients. No deployment test below makes a Groq API request.

## eSpeak NG

Install and inspect the local executable:

```sh
sudo apt install -y espeak-ng
command -v espeak-ng
espeak-ng --version
test_wav=$(mktemp /tmp/vihaan-espeak-XXXXXX.wav)
if ! espeak-ng -w "$test_wav" -- "VIHAAN speech test" \
    || ! test -s "$test_wav"; then
    rm -f "$test_wav"
    echo "eSpeak NG did not produce a WAV file." >&2
    exit 1
fi
rm -f "$test_wav"
```

Generating a WAV verifies synthesis without needing a connected speaker. The
assistant saves eSpeak output to a temporary WAV and delegates playback to the
speaker abstraction; it does not ask eSpeak to play the same response directly.
If `command -v` fails, `TextToSpeech` reports that eSpeak NG is unavailable.
Audible output cannot be verified until a supported audio device is connected.

## Manual startup and tests (required before systemd)

From `~/AI_PIN`, with the virtual environment active and `.env` configured:

```sh
python main.py
```

With PyAudio omitted, the simulation uses silent microphone frames and a
log-only simulated speaker. The interactive simulated button prompts for
Enter to start and stop a recording. Silence is rejected before cloud calls;
this verifies startup, event handling, and clean return to ready without a
mic, amp, speaker, or button. Press Ctrl+C to shut down.

Run the software tests without contacting Groq or requiring hardware:

```sh
python -m pytest -q -p no:cacheprovider
```

Run configuration, executable, network, and simulation checks:

```sh
python -m pytest tests/test_config.py tests/test_ai.py \
    tests/test_network_manager.py tests/test_hardware.py \
    tests/test_assistant.py -q -p no:cacheprovider
```

Confirm logs do not contain the API key or user audio/transcript contents.
`data/logs/vihaan.log` rotates at 2 MiB with two backups; `data/cache/` holds
short-lived WAVs and should be empty after each completed interaction.

## Hardware connections — not for the current unsoldered board

The only exact GPIO assignment currently encoded in the implementation is:

| Part | Code expectation |
|---|---|
| Push-to-talk button | `BUTTON_GPIO_PIN=17`, BCM numbering (physical header pin 11); active-low to GND with the internal pull-up and 200 ms debounce. |
| INMP441 | `PiMicrophone` opens the default ALSA input through PyAudio; no I2S pin numbers, ALSA card/device index, overlay, or device-tree setup are selected in code. |
| MAX98357A | `PiSpeaker` opens the default ALSA output through PyAudio; no I2S pin numbers, ALSA card/device index, overlay, or device-tree setup are selected in code. |

Do not solder or connect hardware based on an assumed I2S pin map. Before
hardware activation, select compatible Raspberry Pi I2S overlays and confirm
their PCM signal mapping against the exact INMP441/MAX98357A breakout
documentation. Both modules must appear as the expected ALSA default devices,
or the code needs an explicit device selection in a later hardware-validation
change. The display is a stub and camera is disabled; neither is needed.

At signal level, the INMP441 data output must reach the Pi's I2S capture input,
and the MAX98357A digital input must receive the Pi's I2S playback output;
both use the selected I2S bit-clock and word-select signals with a common
ground. Supply voltage and the microphone's L/R selection must follow each
breakout's own documentation. The current source does not select the Pi header
pins or overlay, so this is not a wiring-ready pin map.

When the header is soldered and devices are connected, set `HARDWARE_MODE=auto`
only after checking the actual pin/overlay setup. Install/validate PyAudio and
PortAudio, plus the `RPi.GPIO`-compatible package required by `PiButton`, on
the target OS then. Package availability and permissions are OS-image-specific;
inspect them with
`apt-cache policy python3-rpi.gpio portaudio19-dev libasound2-dev` before
installation. Do not run the physical test checklist before the hardware is
assembled.

## Optional systemd service (manual test first)

The template at `deployment/vihaan.service` is deliberately **not enabled**.
It runs as a dedicated `vihaan` user, loads its key from an external
environment file, uses bounded failure restarts, and writes app logs under the
project's `data/` directory. Keep it in simulation mode until physical hardware
has been completed and tested.

After manual tests pass, prepare a root-owned code checkout and a service
account. Check first so these commands do not overwrite existing accounts or
files:

```sh
getent passwd vihaan
getent group vihaan
test ! -e /opt/vihaan/AI_PIN
```

Create only whichever account/group is missing. If the project directory
already exists, inspect it and choose an intentional path instead of deleting
or replacing it:

```sh
if ! getent group vihaan >/dev/null; then
    sudo groupadd --system vihaan
fi
if ! getent passwd vihaan >/dev/null; then
    sudo useradd --system --gid vihaan --home-dir /var/lib/vihaan \
        --create-home --shell /usr/sbin/nologin vihaan
fi
sudo install -d -o root -g root -m 0755 /opt/vihaan
sudo git clone https://github.com/tanveersingh0902/AI_PIN.git \
    /opt/vihaan/AI_PIN
sudo python3 -m venv /opt/vihaan/venv
sudo /opt/vihaan/venv/bin/python -m pip install --upgrade pip
sudo /opt/vihaan/venv/bin/python -m pip install \
    -c /opt/vihaan/AI_PIN/deployment/armv6-constraints.txt \
    -r /opt/vihaan/AI_PIN/deployment/requirements-pi-simulation.txt
sudo install -d -o vihaan -g vihaan -m 0750 \
    /opt/vihaan/AI_PIN/data/cache /opt/vihaan/AI_PIN/data/logs
sudo install -d -o root -g vihaan -m 0750 /etc/vihaan
sudoedit /etc/vihaan/vihaan.env
sudo chown root:vihaan /etc/vihaan/vihaan.env
sudo chmod 0640 /etc/vihaan/vihaan.env
```

Put only the required settings in the protected environment file, for example
`GROQ_API_KEY=...` and `HARDWARE_MODE=simulation`. Do not put credentials in
the unit. Validate the service user's manual start before installing the unit:

```sh
sudo -u vihaan sh -c \
  'set -a; . /etc/vihaan/vihaan.env; set +a; cd /opt/vihaan/AI_PIN && /opt/vihaan/venv/bin/python -m pytest -q -p no:cacheprovider'
sudo -u vihaan sh -c \
  'set -a; . /etc/vihaan/vihaan.env; set +a; cd /opt/vihaan/AI_PIN && /opt/vihaan/venv/bin/python main.py'
```

Stop the manual run with Ctrl+C and confirm clean shutdown before proceeding.
Then install and inspect the unit; **do not enable it yet**:

```sh
sudo install -m 0644 /opt/vihaan/AI_PIN/deployment/vihaan.service \
    /etc/systemd/system/vihaan.service
sudo systemd-analyze verify /etc/systemd/system/vihaan.service
sudo systemctl daemon-reload
sudo systemctl start vihaan
sudo systemctl status vihaan --no-pager
sudo journalctl -u vihaan -f
```

To control it after manual validation:

```sh
sudo systemctl stop vihaan
sudo systemctl restart vihaan
sudo journalctl -u vihaan --since today --no-pager
sudo systemctl disable vihaan
```

Only after explicit manual validation should automatic startup be considered:
`sudo systemctl enable vihaan`. `network-online.target` is an ordering hint,
not proof that internet/Groq is reachable; the application already handles
offline startup and checks again on later button events. `Restart=on-failure`
plus the start limit prevents an aggressive restart loop.

## Deployment acceptance checklist

- [ ] Confirm board model, `armv6l`, 32-bit word size, `armhf`, OS release, and actual Python version before package installation.
- [ ] Confirm the OS image is current Raspberry Pi OS Lite 32-bit offered for the original Zero W.
- [ ] Create the virtual environment and install the ARMv6 simulation profile; run `pip check` and import Groq/Pydantic.
- [ ] Confirm `GROQ_API_KEY` is present without displaying its value; verify `.env` permissions and Git ignore behavior.
- [ ] Run `espeak-ng --version` and synthesize a temporary WAV; remove the WAV.
- [ ] Run `pytest` with mocks; confirm no physical devices or Groq calls are required.
- [ ] Run `main.py` in `HARDWARE_MODE=simulation`; verify ready state, simulated button events, silence rejection, logs, and Ctrl+C shutdown.
- [ ] Check the protected service environment file and verify the systemd unit with `systemd-analyze verify`.
- [ ] Test manual startup as the service user before `systemctl start`; do not enable boot startup beforehand.
- [ ] Record all failures and package versions. Do not claim ARMv6 compatibility until the Pi install and test suite actually pass.

## After the header is soldered

Only then begin physical tests: confirm I2S overlay/device mapping, ALSA input and
output enumeration, microphone sample format and capture, GPIO17 active-low
button/debounce, MAX98357A playback, eSpeak WAV playback, hardware permissions,
and cleanup on interruption. Measure memory/CPU during repeat interactions.
Physical hardware is not yet assembled or tested.
