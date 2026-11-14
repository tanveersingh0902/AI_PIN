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

## 🧠 Architecture (Steps 3–6)

| Component | Technology | Runs on |
|---|---|---|
| **Speech-to-Text** | Groq Whisper `whisper-large-v3-turbo` | ☁️ Cloud |
| **Language Model** | Groq `openai/gpt-oss-120b` | ☁️ Cloud |
| **Text-to-Speech** | `espeak-ng` (local executable) | 💻 Device |

### Module responsibilities and workflow

```
Push-to-talk press → record until release → temporary WAV
                                            ↓
                             Groq Whisper transcription
                                            ↓
                              Groq LLM + conversation history
                                            ↓
                   local eSpeak NG WAV → hardware speaker playback
                                            ↓
                                    return to IDLE
```

`main.py` loads settings, configures logging, constructs the hardware kit and AI clients, then starts `assistant.controller.AssistantController`. The controller owns button events, assistant state, recording validation, offline checks, response synthesis/playback, and temporary-file cleanup. `ai.pipeline.AIPipeline` coordinates STT, LLM, and conversation history; `ai.speech_to_text` and `ai.llm` own Groq requests/retries; `ai.text_to_speech` invokes local eSpeak NG. `hardware.factory` selects real or simulated input/output, while `backend.network_manager` is hardware-independent.

The `backend.pipeline.py`, `backend.state.py`, and `backend.session.py` files are earlier Step 1 scaffolding, not used by `main.py`. Likewise, `ai/stt.py` and `ai/tts.py` are superseded stubs. `network/api_client.py` is a generic requests helper, not used by Groq. Wake-word, LED, camera capture, and SPI display implementations are not part of the active assistant workflow.

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

## Step 6: Full-System Verification

Run the complete offline test suite from the project root:

```powershell
python -m pytest -q
```

Focused suites can be run with `python -m pytest tests/test_assistant.py tests/test_ai.py -q`, `python -m pytest tests/test_hardware.py -q`, or `python -m pytest tests/test_network_manager.py -q`. Groq requests, eSpeak subprocesses, audio devices, and connectivity probes are mocked in tests. No API key, internet access, or Raspberry Pi is needed to run the test suite.

The tests verify the event-driven voice workflow, conversation history, offline and mid-request recovery, bounded retries, simulated Windows hardware, temporary-file cleanup, and failure handling. They do not prove physical microphone quality, GPIO debounce behavior, Wi-Fi reachability on the Pi, or actual I2S playback.

## Step 5: Networking and Offline Recovery

`backend/network_manager.py` reports Wi-Fi association separately from internet access. Wi-Fi status is read-only and platform-specific where detectable (Windows `netsh`; Linux wireless tools/sysfs); unsupported or unavailable status is reported as unknown. Internet reachability uses a short TCP connection check to `1.1.1.1:443`. A Wi-Fi connection alone is not treated as internet access. Diagnostics report whether the Groq key is configured, never its value, and retain the timestamp of the last successful check.

The application checks connectivity at startup for diagnostics and again before each cloud pipeline run. It does not poll in a background thread, change OS network settings, or try to reconnect Wi-Fi itself. `wait_for_connectivity()` is available for bounded, explicitly requested waits; normal assistant use does not block waiting for the network.

The Groq clients use the configured request timeout and disable SDK-internal retries so the application owns retry policy. Transient connection/timeout, HTTP 408/409/429, and server errors receive a configurable, bounded exponential backoff (at most five retries); authentication failures are not retried. When already offline, the controller skips cloud calls and uses local eSpeak NG for an offline message. If connectivity drops during a cloud request, the controller checks again and gives the same local feedback. The next button press checks connectivity again, so recovery needs no restart or background service. Cloud transcription and reasoning do not work offline; there is no local-model fallback.

The network settings in `.env` are:

```ini
GROQ_API_KEY=your_groq_api_key
GROQ_TIMEOUT=30
NETWORK_CONNECTION_TIMEOUT=15
CONNECTIVITY_CHECK_TIMEOUT=2
NETWORK_RETRY_COUNT=2
NETWORK_RETRY_DELAY=0.5
```

`NETWORK_CONNECTION_TIMEOUT` is the maximum duration for an explicit connectivity wait. Each reachability probe is bounded by `CONNECTIVITY_CHECK_TIMEOUT`. The retry count is the number of retries after the initial Groq request. Do not put Wi-Fi passwords in `.env`; Raspberry Pi OS manages Wi-Fi separately.

### Windows simulation

The hardware factory selects simulated microphone, button, speaker, and display on Windows. The simulated button uses Enter to start recording and another Enter to release it. When PyAudio is available, the simulated microphone may use the computer's default input device; otherwise, it produces silence, which the controller rejects without making a Groq request. The simulated speaker may use an available local playback backend or log the playback.

To run the application, configure `.env` with a valid `GROQ_API_KEY`, install the Python requirements, and install eSpeak NG if you want audible TTS. Startup diagnostics will perform one short internet check but do not require a successful check to start. Then run:

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
│   ├── led.py                   #    Optional LED scaffold
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
├── assistant/                   # 🎙️ Main application controller
│   └── controller.py            #    Button-driven recording and response loop
│
├── simulation/                  # 🖥️ Simulated hardware (Windows dev)
│   ├── sim_microphone.py        #    Simulated mic
│   ├── sim_speaker.py           #    Simulated speaker
│   ├── sim_button.py            #    Simulated button
│   ├── sim_display.py           #    Simulated display
│   ├── sim_camera.py            #    Simulated camera interface
│   └── sim_led.py               #    Simulated LED
│
├── backend/                     # ⚙️ Application logic
│   ├── network_manager.py       #    Wi-Fi/internet status and diagnostics
│   ├── pipeline.py              #    Earlier unused pipeline scaffold
│   ├── state.py                 #    Earlier unused device state machine
│   └── session.py               #    Earlier unused session manager
│
├── network/                     # 🌐 Connectivity
│   ├── wifi.py                  #    Read-only Wi-Fi status detection
│   ├── retry.py                 #    Bounded transient Groq request retries
│   ├── bluetooth.py             #    Bluetooth (future)
│   └── api_client.py            #    Optional generic requests helper
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
├── deployment/                  # 🍓 Pi Zero W deployment preparation
│   ├── README.md                #    ARMv6 preflight, setup, operation, checklist
│   ├── requirements-pi-simulation.txt
│   ├── armv6-constraints.txt    #    Pydantic v1 compatibility profile
│   └── vihaan.service          #    Optional; not enabled automatically
│
└── tests/                       # 🧪 Offline unit tests
    ├── test_ai.py               #    AI pipeline tests (mocked)
    ├── test_hardware.py         #    Hardware abstraction tests
    ├── test_config.py           #    Configuration tests
    ├── test_pipeline.py         #    Backend pipeline tests
    ├── test_assistant.py        #    Integrated assistant tests
    ├── test_network_manager.py  #    Offline connectivity and retry tests
    ├── test_deployment.py       #    Static Pi deployment checks
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

## Step 7: Raspberry Pi Zero W deployment preparation

The original Zero W uses an ARMv6 CPU. Before installing anything, verify the
actual board, OS release, word size, architecture, and Python version on the
device. `HARDWARE_MODE=simulation` supports an SSH-only start without
initializing GPIO or I2S drivers. The Pi simulation dependency profile omits
PyAudio/PortAudio; its microphone is silent and its speaker is log-only.

Follow the deployment guide for OS selection, ARMv6 dependency caveats, secure
Groq configuration, 2.4 GHz Wi-Fi and OnePlus hotspot setup, eSpeak NG,
manual tests, and the optional manual-first systemd service:

**[Raspberry Pi Zero W deployment guide](deployment/README.md)**

No Raspberry Pi software install, ARMv6 build, or physical hardware test has
been performed from this Windows workspace. The current I2S drivers do not
specify a pin/overlay mapping, so do not connect them based on an assumed map.
The only source-defined hardware pin is the active-low push-to-talk button on
BCM GPIO17 (physical pin 11).

---

## 🏛️ Architecture Principles

| Principle | How It's Applied |
|---|---|
| **Hardware Isolation** | `hardware/` defines interfaces; the factory selects real or simulated components |
| **Cloud AI, Local TTS** | STT + LLM on Groq cloud; eSpeak NG runs locally |
| **Single API Key** | One `GROQ_API_KEY` for both Whisper STT and LLM |
| **Memory-Conscious** | 384 MB is a target budget, not an enforced process limit; history is capped at 10 turns |
| **Dependency Injection** | HardwareFactory auto-selects real vs simulated drivers |
| **Config-Driven** | All tunables in `.env` — no hardcoded secrets |
| **Network Resilience** | Read-only connectivity checks and bounded Groq retries; local offline feedback |
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

The software is designed for a **~384 MB working budget**, but the application does not currently enforce a memory cap. It reduces memory use by:
1. Offloading STT + LLM to Groq cloud API
2. Using eSpeak NG (< 5 MB) for local TTS
3. No PyTorch, TensorFlow, or local AI models
4. Capping conversation history at 10 turns
5. Streaming WAV playback in chunks on the Pi hardware path

---

## 📜 License

Private project — all rights reserved.
