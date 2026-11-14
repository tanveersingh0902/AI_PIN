"""
ai — Artificial Intelligence Layer
====================================
Handles speech recognition (STT), text-to-speech (TTS), large language
model (LLM) interaction, conversation management, and the AI pipeline.

All heavy AI processing uses Groq's cloud API to keep the Pi's RAM free.
TTS runs locally via eSpeak NG.

Modules
-------
- speech_to_text.py : Groq Whisper STT (cloud)
- llm.py            : Groq LLM chat completion (cloud)
- text_to_speech.py : eSpeak NG TTS (local subprocess)
- conversation.py   : Conversation history manager
- pipeline.py       : AI pipeline orchestrator (STT → LLM → TTS)
- wake_word.py      : Wake-word ("Hey Vihaan") detection (future)

Legacy stubs (from Step 1, superseded):
- stt.py            : Superseded by speech_to_text.py
- tts.py            : Superseded by text_to_speech.py
"""
