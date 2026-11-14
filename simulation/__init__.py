"""
simulation — Simulated Hardware for Windows Development
========================================================
Drop-in replacements for the hardware/ drivers that work on
Windows (or any non-Pi platform). They implement the same
abstract interfaces (BaseMicrophone, BaseSpeaker, etc.) so the
rest of the codebase doesn't need to know whether it's running
on real hardware or not.

Modules
-------
- sim_mic.py     : Simulated microphone (reads from WAV files or system mic)
- sim_speaker.py : Simulated speaker (plays via Windows audio)
- sim_button.py  : Simulated button (keyboard key press)
- sim_led.py     : Simulated LED (console / terminal output)
"""
