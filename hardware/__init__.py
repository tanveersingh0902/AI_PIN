"""
hardware — Hardware Abstraction Layer
======================================
Drivers for physical peripherals on the Raspberry Pi Zero W.

Each module defines an abstract interface (ABC) and a concrete
Pi implementation.  The simulation/ package provides drop-in
replacements for development on non-Pi platforms.

Use hardware.factory.HardwareFactory.create() to get the correct
implementations for the current platform.

Modules
-------
- microphone.py : Microphone input (INMP441 I2S)
- speaker.py    : Audio output (MAX98357A I2S amplifier)
- button.py     : Push-to-talk button (GPIO17)
- display.py    : Optional SPI TFT display
- camera.py     : Optional camera (CSI / USB)
- led.py        : Status LED(s) via GPIO
- battery.py    : Battery voltage reading via ADC (SPI)
- factory.py    : Hardware factory — dependency injection
"""
