"""
backend — Application Logic Layer
===================================
Orchestrates the voice assistant pipeline and manages application state.
This layer is platform-independent — it depends on abstract interfaces
from hardware/ (or simulation/) and ai/.

Modules
-------
- pipeline.py : Main voice-assistant loop (listen → think → speak)
- state.py    : Device state machine (idle, listening, thinking, speaking)
- session.py  : Conversation session and short-term memory
"""
