# 🔲 VIHAAN AI PIN

> **Wearable AI Voice Assistant** powered by Raspberry Pi Zero W

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20Zero%20W-green.svg)](https://www.raspberrypi.org/)
[![Tests](https://img.shields.io/badge/Tests-offline-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

---

## 📖 Overview

VIHAAN AI PIN is a compact, wearable AI voice assistant designed for a **Raspberry Pi Zero W** (512 MB RAM). The user holds a push-to-talk button while speaking; speech is sent to Groq for recognition and reasoning, and the response is spoken locally.

**Development** happens on Windows 11 with VS Code. **Deployment** targets Raspberry Pi OS Lite (32-bit). The architecture separates hardware from logic; the Pi hardware path has not yet been physically tested.

---

## 🧠 AI Architecture (Steps 3 and 4)

| Component | Technology | Runs on |
|---|---|---|
| **Speech-to-Text** | Groq Whisper `whisper-large-v3-turbo` | ☁️ Cloud |
| **Language Model** | Groq `openai/gpt-oss-120b` | ☁️ Cloud |
| **Text-to-Speech** | `espeak-ng` (local executable) | 💻 Device |

### Voice Workflow

```
Push-to-talk press → record until release → temporary WAV
                                            ↓
                             Groq Whisper transcription
                                            ↓
                              Groq LLM + conversation history
                                            ↓
                   local eSpeak NG WAV → hardware speaker playback
```

### Internet Requirements

| Component | Internet Required? |
|---|---|
| Speech-to-Text (Groq Whisper) | ✅ Yes |
| LLM (Groq) | ✅ Yes |
| Text-to-Speech (eSpeak NG) | ❌ No — runs locally |
| Hardware (mic, speaker, button) | ❌ No |

---

## Step 4: Main Assistant Integration

`assistant/controller.py` coordinates the existing hardware abstractions and `ai.pipeline.AIPipeline`; it does not implement GPIO or duplicate the AI clients. Button callbacks only enqueue press/release events. The controller starts microphone capture on press, writes and validates the recording on release, and invokes the existing STT/LLM pipeline with direct TTS disabled. It then asks local eSpeak NG to create a WAV and plays that WAV once through the speaker abstraction. Conversation history remains in memory between interactions, and temporary recording/speech files are removed after each interaction.

The controller owns `INITIALIZING`, `IDLE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `ERROR`, and `SHUTDOWN` states. Recoverable errors are logged and return the assistant to `IDLE`. Optional display updates use the existing display abstraction; display failures do not stop the voice workflow. Cloud requests happen only after a non-silent recording is validated and the push-to-talk button is released.

The model identifiers are fixed in the application: `whisper-large-v3-turbo` and `openai/gpt-oss-120b`. The only credential is `GROQ_API_KEY`. Unit tests mock the Groq clients and eSpeak output; they do not contact Groq or require physical hardware.

### Windows simulation

The hardware factory selects simulated microphone, button, speaker, and display on Windows. The simulated button uses Enter to start recording and another Enter to release it. When PyAudio is available, the simulated microphone may use the computer's default input device; otherwise, it produces silence, which the controller rejects without making a Groq request. The simulated speaker may use an available local playback backend or log the playback.

To run the application, configure `.env` with a valid `GROQ_API_KEY`, install the Python requirements, and install eSpeak NG if you want audible TTS. Then run:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Press Enter once, speak while recording, then press Enter again. If the simulated microphone produces silence or no usable input, the assistant skips the API calls and returns to ready. Press Ctrl+C to shut down.

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
│   ├── pipeline.py              #    Earlier pipeline scaffold
│   ├── state.py                 #    Device state machine
│   └── session.py               #    Session manager
│
├── assistant/                   # 🎙️ Main application controller
│   └── controller.py            #    Button-driven recording and response loop
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
│   └── models/                  #    Reserved; no local AI models are used
│
└── tests/                       # 🧪 Offline unit tests
    ├── test_ai.py               #    AI pipeline tests (mocked)
    ├── test_hardware.py         #    Hardware abstraction tests
    ├── test_config.py           #    Configuration tests
    ├── test_pipeline.py         #    Backend pipeline tests
    ├── test_assistant.py        #    Integrated assistant tests
    └── test_platform.py         #    Platform detection tests
```

---

## 🚀 Quick Start (Windows Development)

### 1. Clone & Setup

```powershell
git clone https://github.com/tanveersingh0902/AI_PIN.git
cd AI_PIN
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure API Key

```powershell
copy .env.example .env
```

Edit `.env` and set your Groq API key:

```
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

Get a free key at: https://console.groq.com/keys

### 3. Install eSpeak NG for speech output

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

The tests use mocked API clients and simulated hardware; they run without internet, API keys, or physical Raspberry Pi hardware.

---

## 🍓 Deployment (Raspberry Pi Zero W)

### Prerequisites

- Raspberry Pi Zero W with Raspberry Pi OS Lite (32-bit); the 40-pin header must be soldered before GPIO wiring
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
pip install RPi.GPIO
```

### Configure and run

```bash
cp .env.example .env
nano .env  # Set GROQ_API_KEY
python3 main.py
```

Enable and configure I2S/ALSA for the microphone and amplifier before using real audio hardware. **Hardware has not been assembled or physically tested.** The current Pi microphone/speaker drivers require working PyAudio/ALSA configuration. The Pi display driver is still a stub; this step does not implement the deferred SPI display.

---

## 🏛️ Architecture Principles

| Principle | How It's Applied |
|---|---|
| **Hardware Isolation** | `hardware/` defines interfaces; the factory selects real or simulated components |
| **Cloud AI, Local TTS** | STT + LLM on Groq cloud; eSpeak NG runs locally |
| **Single API Key** | One `GROQ_API_KEY` for both Whisper STT and LLM |
| **Memory-Conscious** | 384 MB soft cap; capped conversation history (10 turns) |
| **Dependency Injection** | HardwareFactory auto-selects real vs simulated drivers |
| **Config-Driven** | All tunables in `.env` — no hardcoded secrets |
| **Fully Testable** | Tests run offline with mocked APIs and simulated hardware |

---

## 📋 Development Roadmap

- [x] Step 1: Project structure & foundation
- [x] Step 2: Hardware abstraction layer
- [x] Step 3: AI pipeline (STT + LLM + TTS)
- [x] Step 4: Main application integration
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
