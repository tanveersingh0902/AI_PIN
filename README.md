# 🔲 VIHAAN AI PIN

> **Wearable AI Voice Assistant** powered by Raspberry Pi Zero W

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20Zero%20W-green.svg)](https://www.raspberrypi.org/)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

---

## 📖 Overview

VIHAAN AI PIN is a compact, wearable AI voice assistant designed to run on a **Raspberry Pi Zero W** (512 MB RAM). It listens for a wake word, captures speech, sends it to a cloud LLM, and speaks the response — all through a pin-sized form factor.

**Development** happens on Windows 11 with VS Code. **Deployment** targets Raspberry Pi OS Lite (32-bit). The architecture cleanly separates hardware from logic so the same codebase works on both platforms.

---

## 🏗️ Project Structure

```
AI_PIN/
├── main.py                  # Entry point — launches the assistant
├── config.py                # Central configuration (env vars + defaults)
├── requirements.txt         # Python dependencies
├── .env.example             # Template for secrets / settings
├── .gitignore               # Git exclusions
├── README.md                # This file
│
├── hardware/                # 🔧 Real hardware drivers (Pi only)
│   ├── __init__.py
│   ├── mic.py               #    Microphone input (I2S / USB)
│   ├── speaker.py           #    Audio output (I2S DAC / 3.5mm)
│   ├── button.py            #    Physical push-button (GPIO)
│   ├── led.py               #    Status LED (GPIO)
│   └── battery.py           #    Battery voltage monitor (SPI ADC)
│
├── ai/                      # 🧠 AI / ML layer
│   ├── __init__.py
│   ├── stt.py               #    Speech-to-Text engine
│   ├── tts.py               #    Text-to-Speech engine
│   ├── llm.py               #    LLM client (Gemini / OpenAI)
│   └── wake_word.py         #    Wake-word detection
│
├── network/                 # 🌐 Connectivity
│   ├── __init__.py
│   ├── wifi.py              #    Wi-Fi status & management
│   ├── bluetooth.py         #    Bluetooth (future)
│   └── api_client.py        #    Shared HTTP client with retries
│
├── backend/                 # ⚙️ Application logic
│   ├── __init__.py
│   ├── pipeline.py          #    Voice assistant loop (listen→think→speak)
│   ├── state.py             #    Device state machine
│   └── session.py           #    Conversation history / memory
│
├── simulation/              # 🖥️ Simulated hardware (Windows dev)
│   ├── __init__.py
│   ├── sim_mic.py           #    Simulated microphone
│   ├── sim_speaker.py       #    Simulated speaker
│   ├── sim_button.py        #    Simulated button (keyboard)
│   └── sim_led.py           #    Simulated LED (console output)
│
├── utils/                   # 🛠️ Shared utilities
│   ├── __init__.py
│   ├── logger.py            #    Logging setup (console + file)
│   ├── platform_detect.py   #    Detect Windows vs Pi at runtime
│   └── helpers.py           #    Misc helper functions
│
├── data/                    # 📁 Runtime data (gitignored contents)
│   ├── logs/                #    Application log files
│   ├── cache/               #    Temporary cache
│   └── models/              #    Offline AI models (if any)
│
└── tests/                   # 🧪 Test suite
    ├── __init__.py
    ├── test_config.py       #    Configuration tests
    ├── test_platform.py     #    Platform detection tests
    └── test_pipeline.py     #    Pipeline & state machine tests
```

---

## 🚀 Quick Start (Windows Development)

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd AI_PIN
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
python main.py
```

### 4. Test

```bash
pytest tests/ -v
```

---

## 🍓 Deployment (Raspberry Pi Zero W)

### Prerequisites

- Raspberry Pi Zero W with Raspberry Pi OS Lite (32-bit)
- Python 3.9+
- I2S microphone (e.g., INMP441)
- Speaker / DAC (e.g., MAX98357A)
- Push button + LED on GPIO

### Install

```bash
# On the Pi:
sudo apt update && sudo apt install -y python3-pip python3-venv
git clone <your-repo-url>
cd AI_PIN
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Pi-specific dependencies:
pip install RPi.GPIO gpiozero spidev
```

### Run

```bash
python3 main.py
```

---

## 🏛️ Architecture Principles

| Principle | How It's Applied |
|---|---|
| **Hardware Isolation** | `hardware/` is never imported on Windows; `simulation/` provides drop-in replacements |
| **Lightweight by Default** | Cloud APIs for heavy AI; pyttsx3/espeak for offline TTS |
| **Memory-Conscious** | 384 MB soft cap; capped conversation history; response size limits |
| **Cross-Platform** | `platform_detect.py` auto-selects real vs simulated drivers |
| **Modular** | Each folder is an independent layer with clean interfaces |
| **Config-Driven** | All tunables in `.env` — no hard-coded secrets or magic numbers |

---

## 📋 Development Roadmap

- [x] Project structure & foundation
- [ ] Platform detection & simulation layer
- [ ] Speech-to-Text (Google Web Speech)
- [ ] Text-to-Speech (pyttsx3)
- [ ] LLM integration (Gemini API)
- [ ] Wake-word detection
- [ ] Voice pipeline end-to-end
- [ ] GPIO hardware drivers
- [ ] Battery monitoring
- [ ] Bluetooth audio
- [ ] 3D-printed enclosure design

---

## 🛡️ Resource Constraints

The Raspberry Pi Zero W has:
- **CPU**: 1 GHz single-core ARM11 (ARMv6)
- **RAM**: 512 MB (shared with GPU)
- **Storage**: microSD
- **Connectivity**: Wi-Fi 802.11n, Bluetooth 4.1

The software is designed to run within **~384 MB RAM** by:
1. Offloading AI inference to cloud APIs
2. Using lightweight libraries (no PyTorch, no TensorFlow)
3. Capping conversation history and cache sizes
4. Using streaming audio (never buffering entire recordings)

---

## 📜 License

Private project — all rights reserved.
