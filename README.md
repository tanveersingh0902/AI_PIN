# 🔲 VIHAAN AI PIN

> **Wearable AI Voice Assistant** powered by Raspberry Pi Zero W

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20Zero%20W-green.svg)](https://www.raspberrypi.org/)
[![Tests](https://img.shields.io/badge/Tests-99%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

---

## 📖 Overview

VIHAAN AI PIN is a compact, wearable AI voice assistant designed to run on a **Raspberry Pi Zero W** (512 MB RAM). It listens for a wake word, captures speech, sends it to a cloud LLM, and speaks the response — all through a pin-sized form factor.

**Development** happens on Windows 11 with VS Code. **Deployment** targets Raspberry Pi OS Lite (32-bit). The architecture cleanly separates hardware from logic so the same codebase works on both platforms.

---

## 🧠 AI Architecture (Step 3)

| Component | Technology | Runs on |
|---|---|---|
| **Speech-to-Text** | Groq Whisper `whisper-large-v3-turbo` | ☁️ Cloud |
| **Language Model** | Groq `openai/gpt-oss-120b` | ☁️ Cloud |
| **Text-to-Speech** | `espeak-ng` (local executable) | 💻 Device |

### Pipeline Flow

```
🎤 Microphone → Audio file
                    ↓
         Groq Whisper STT (cloud)
                    ↓
            Transcribed text
                    ↓
         Groq LLM (cloud)
                    ↓
           Generated response
                    ↓
         eSpeak NG TTS (local)
                    ↓
               🔊 Speaker
```

### Internet Requirements

| Component | Internet Required? |
|---|---|
| Speech-to-Text (Groq Whisper) | ✅ Yes |
| LLM (Groq) | ✅ Yes |
| Text-to-Speech (eSpeak NG) | ❌ No — runs locally |
| Hardware (mic, speaker, button) | ❌ No |

---

## 🏗️ Project Structure

```
AI_PIN/
├── main.py                      # Entry point — launches the assistant
├── config.py                    # Central configuration (env vars + defaults)
├── requirements.txt             # Python dependencies
├── .env.example                 # Template for secrets / settings
├── .gitignore                   # Git exclusions
├── README.md                    # This file
│
├── hardware/                    # 🔧 Hardware abstraction (Pi drivers)
│   ├── microphone.py            #    INMP441 I2S microphone
│   ├── speaker.py               #    MAX98357A I2S amplifier
│   ├── button.py                #    GPIO17 push-to-talk button
│   ├── display.py               #    Optional SPI TFT display
│   ├── camera.py                #    Optional camera (CSI/USB)
│   └── factory.py               #    Hardware factory (DI)
│
├── ai/                          # 🧠 AI pipeline
│   ├── speech_to_text.py        #    Groq Whisper STT
│   ├── llm.py                   #    Groq LLM client
│   ├── text_to_speech.py        #    eSpeak NG TTS
│   ├── conversation.py          #    Conversation history manager
│   ├── pipeline.py              #    AI pipeline orchestrator
│   └── wake_word.py             #    Wake-word detection (future)
│
├── simulation/                  # 🖥️ Simulated hardware (Windows dev)
│   ├── sim_microphone.py        #    Simulated mic
│   ├── sim_speaker.py           #    Simulated speaker
│   ├── sim_button.py            #    Simulated button
│   └── sim_display.py           #    Simulated display
│
├── backend/                     # ⚙️ Application logic
│   ├── pipeline.py              #    Voice assistant loop
│   ├── state.py                 #    Device state machine
│   └── session.py               #    Session manager
│
├── network/                     # 🌐 Connectivity
│   ├── wifi.py                  #    Wi-Fi management
│   ├── bluetooth.py             #    Bluetooth (future)
│   └── api_client.py            #    Shared HTTP client
│
├── utils/                       # 🛠️ Shared utilities
│   ├── logger.py                #    Logging setup
│   ├── platform_detect.py       #    OS detection
│   └── helpers.py               #    Helper functions
│
├── data/                        # 📁 Runtime data
│   ├── logs/                    #    Log files
│   ├── cache/                   #    Temporary cache
│   └── models/                  #    Offline models (if any)
│
└── tests/                       # 🧪 Test suite (99 tests)
    ├── test_ai.py               #    AI pipeline tests (mocked)
    ├── test_hardware.py         #    Hardware abstraction tests
    ├── test_config.py           #    Configuration tests
    ├── test_pipeline.py         #    Backend pipeline tests
    └── test_platform.py         #    Platform detection tests
```

---

## 🚀 Quick Start (Windows Development)

### 1. Clone & Setup

```bash
git clone https://github.com/tanveersingh0902/AI_PIN.git
cd AI_PIN
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
copy .env.example .env
```

Edit `.env` and set your Groq API key:

```
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

Get a free key at: https://console.groq.com/keys

### 3. Install eSpeak NG (optional for dev)

eSpeak NG is a **system executable**, not a pip package.

**Windows:**
Download from https://github.com/espeak-ng/espeak-ng/releases and install. The installer adds it to PATH.

**Raspberry Pi:**
```bash
sudo apt install espeak-ng
```

### 4. Run

```bash
python main.py
```

### 5. Test

```bash
pytest tests/ -v
```

All 99 tests run **without internet, API keys, or hardware**.

---

## 🍓 Deployment (Raspberry Pi Zero W)

### Prerequisites

- Raspberry Pi Zero W with Raspberry Pi OS Lite (32-bit)
- Python 3.9+
- INMP441 I2S microphone
- MAX98357A I2S amplifier + speaker
- Push-to-talk button on GPIO17

### Install

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv espeak-ng
git clone https://github.com/tanveersingh0902/AI_PIN.git
cd AI_PIN
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install RPi.GPIO gpiozero  # Pi-specific
```

### Configure

```bash
cp .env.example .env
nano .env  # Set GROQ_API_KEY
```

### Run

```bash
python3 main.py
```

---

## 🏛️ Architecture Principles

| Principle | How It's Applied |
|---|---|
| **Hardware Isolation** | `hardware/` uses ABCs; `simulation/` provides Windows replacements |
| **Cloud AI, Local TTS** | STT + LLM on Groq cloud; eSpeak NG runs locally |
| **Single API Key** | One `GROQ_API_KEY` for both Whisper STT and LLM |
| **Memory-Conscious** | 384 MB soft cap; capped conversation history (10 turns) |
| **Dependency Injection** | HardwareFactory auto-selects real vs simulated drivers |
| **Config-Driven** | All tunables in `.env` — no hardcoded secrets |
| **Fully Testable** | 99 tests run offline with mocked APIs and hardware |

---

## 📋 Development Roadmap

- [x] Step 1: Project structure & foundation
- [x] Step 2: Hardware abstraction layer
- [x] Step 3: AI pipeline (STT + LLM + TTS)
- [ ] Step 4: Main application integration
- [ ] Wake-word detection
- [ ] GPIO hardware drivers (on Pi)
- [ ] Battery monitoring
- [ ] 3D-printed enclosure

---

## 🛡️ Resource Constraints

The Raspberry Pi Zero W has:
- **CPU**: 1 GHz single-core ARM11 (ARMv6)
- **RAM**: 512 MB (shared with GPU)
- **Storage**: microSD
- **Connectivity**: Wi-Fi 802.11n, Bluetooth 4.1

The software runs within **~384 MB RAM** by:
1. Offloading STT + LLM to Groq cloud API
2. Using eSpeak NG (< 5 MB) for local TTS
3. No PyTorch, TensorFlow, or local AI models
4. Capping conversation history at 10 turns
5. Lightweight Groq SDK (~2 MB installed)

---

## 📜 License

Private project — all rights reserved.
