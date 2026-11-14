"""
ai — Artificial Intelligence Layer
====================================
Handles speech recognition (STT), text-to-speech (TTS), large language
model (LLM) interaction, and wake-word detection.

All AI modules use cloud APIs by default to keep the Pi's RAM free.
Offline alternatives (Vosk, pyttsx3) are available for disconnected use.

Modules
-------
- stt.py        : Speech-to-Text engine
- tts.py        : Text-to-Speech engine
- llm.py        : LLM / chatbot interaction (Gemini / OpenAI)
- wake_word.py  : Wake-word ("Hey Vihaan") detection
"""
