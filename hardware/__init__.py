"""
hardware — Hardware Abstraction Layer
======================================
Drivers for physical peripherals on the Raspberry Pi Zero W.

Each module exposes a base class (interface) and a concrete
implementation that wraps Pi-specific libraries (RPi.GPIO, gpiozero).

These modules are NEVER imported directly on Windows.
The simulation/ package provides drop-in replacements for
development on non-Pi platforms.

Modules
-------
- mic.py      : Microphone input (I2S / USB mic)
- speaker.py  : Audio output (I2S DAC / 3.5 mm / Bluetooth)
- button.py   : Physical push-button via GPIO
- led.py      : Status LED(s) via GPIO
- battery.py  : Battery voltage reading via ADC (SPI)
"""
