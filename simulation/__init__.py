"""
simulation — Simulated Hardware for Windows Development
========================================================
Drop-in replacements for the hardware/ drivers that work on
Windows (or any non-Pi platform).  They implement the same
abstract interfaces so the rest of the codebase stays
platform-independent.

These are instantiated automatically by
hardware.factory.HardwareFactory when not running on a Pi.

Modules
-------
- sim_microphone.py : Simulated mic (system mic via PyAudio, or silence)
- sim_speaker.py    : Simulated speaker (PyAudio / winsound / log-only)
- sim_button.py     : Simulated button (keyboard Enter / programmatic)
- sim_display.py    : Simulated display (console / emoji output)
- sim_camera.py     : Simulated camera (webcam or static placeholder)
- sim_led.py        : Simulated LED (console / emoji output)
"""
