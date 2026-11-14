"""
hardware.factory — Hardware Factory (Dependency Injection)
============================================================
Central factory that detects the runtime platform and returns
the correct hardware implementations:

  - Windows / Linux (dev) → simulated hardware from simulation/
  - Raspberry Pi           → real hardware from hardware/

Pi drivers are imported lazily. Constructor/import failures for
required devices can fall back to simulation, while runtime hardware
errors are surfaced by the component/controller. Optional display or
camera initialization failures do not prevent assistant startup.

Usage
-----
    from hardware.factory import HardwareFactory

    kit = HardwareFactory.create()
    kit.microphone.start_recording()
    ...
    kit.cleanup()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from utils.platform_detect import detect_platform, Platform

logger = logging.getLogger(__name__)


# ── Hardware Kit ───────────────────────────────────────────────

@dataclass
class HardwareKit:
    """
    Container for all hardware component instances.

    Required components (never None):
      - microphone
      - speaker
      - button

    Optional components (may be None):
      - display
      - camera
    """
    microphone: object  # MicrophoneInterface
    speaker: object     # SpeakerInterface
    button: object      # ButtonInterface
    display: Optional[object] = None   # DisplayInterface or None
    camera: Optional[object] = None    # CameraInterface or None
    platform: Platform = Platform.WINDOWS

    def cleanup(self) -> None:
        """Release all hardware resources safely."""
        for name in ("microphone", "speaker", "button", "display", "camera"):
            component = getattr(self, name, None)
            if component is not None:
                try:
                    component.cleanup()
                except Exception as e:
                    logger.warning(f"Cleanup error for {name}: {e}")
        logger.info("HardwareKit: all components cleaned up.")


# ── Factory ────────────────────────────────────────────────────

class HardwareFactory:
    """
    Creates the appropriate hardware implementations based on
    the detected runtime platform.
    """

    @staticmethod
    def create(platform: Platform | None = None,
               sample_rate: int = 16000,
               channels: int = 1,
               chunk_size: int = 1024,
               button_pin: int = 17,
               enable_display: bool = True,
               enable_camera: bool = False) -> HardwareKit:
        """
        Build a HardwareKit with the right implementations.

        Parameters
        ----------
        platform : Platform or None
            Force a specific platform.  None = auto-detect.
        sample_rate : int
            Audio sample rate in Hz.
        channels : int
            Audio channels (1 = mono).
        chunk_size : int
            Audio buffer size in frames.
        button_pin : int
            GPIO pin for the push-to-talk button (Pi only).
        enable_display : bool
            Whether to initialise the display (optional).
        enable_camera : bool
            Whether to initialise the camera (optional, off by default).

        Returns
        -------
        HardwareKit
            A kit with all hardware components ready to use.
        """
        if platform is None:
            platform = detect_platform()

        logger.info(f"HardwareFactory: creating kit for {platform.value}")

        if platform == Platform.RASPBERRY_PI:
            return HardwareFactory._create_pi(
                platform, sample_rate, channels, chunk_size,
                button_pin, enable_display, enable_camera,
            )
        else:
            return HardwareFactory._create_sim(
                platform, sample_rate, channels, chunk_size,
                enable_display,
            )

    # ── Pi hardware ───────────────────────────────────────────

    @staticmethod
    def _create_pi(platform, sample_rate, channels, chunk_size,
                   button_pin, enable_display, enable_camera):
        """Create real Pi hardware with graceful fallback."""

        # ── Microphone ────────────────────────────────────────
        try:
            from hardware.microphone import PiMicrophone
            mic = PiMicrophone(
                sample_rate=sample_rate,
                channels=channels,
                chunk_size=chunk_size,
            )
            logger.info("  ✓ Microphone driver: PiMicrophone (I2S; opened on recording)")
        except Exception as e:
            logger.warning(f"  ✗ PiMicrophone failed ({e}), using SimMicrophone.")
            from simulation.sim_microphone import SimMicrophone
            mic = SimMicrophone(sample_rate=sample_rate, channels=channels)

        # ── Speaker ───────────────────────────────────────────
        try:
            from hardware.speaker import PiSpeaker
            spk = PiSpeaker(chunk_size=chunk_size)
            logger.info("  ✓ Speaker driver: PiSpeaker (I2S; opened on playback)")
        except Exception as e:
            logger.warning(f"  ✗ PiSpeaker failed ({e}), using SimSpeaker.")
            from simulation.sim_speaker import SimSpeaker
            spk = SimSpeaker()

        # ── Button ────────────────────────────────────────────
        try:
            from hardware.button import PiButton
            btn = PiButton(gpio_pin=button_pin)
            logger.info(
                f"  ✓ Button driver: PiButton (GPIO{button_pin}; setup deferred)"
            )
        except Exception as e:
            logger.warning(f"  ✗ PiButton failed ({e}), using SimButton.")
            from simulation.sim_button import SimButton
            btn = SimButton()

        # ── Display (optional) ────────────────────────────────
        display = None
        if enable_display:
            try:
                from hardware.display import PiDisplay
                display = PiDisplay()
                display.init()
                logger.info("  ✓ Display: PiDisplay (SPI TFT)")
            except Exception as e:
                logger.info(f"  ○ Display not available ({e}), skipping.")
                display = None

        # ── Camera (optional, off by default) ─────────────────
        camera = None
        if enable_camera:
            try:
                from hardware.camera import PiCamera
                camera = PiCamera()
                logger.info("  ✓ Camera: PiCamera (CSI)")
            except Exception as e:
                logger.info(f"  ○ Camera not available ({e}), skipping.")
                camera = None

        return HardwareKit(
            microphone=mic, speaker=spk, button=btn,
            display=display, camera=camera, platform=platform,
        )

    # ── Simulated hardware ────────────────────────────────────

    @staticmethod
    def _create_sim(platform, sample_rate, channels, chunk_size,
                    enable_display):
        """Create simulated hardware for Windows / Linux dev."""
        from simulation.sim_microphone import SimMicrophone
        from simulation.sim_speaker import SimSpeaker
        from simulation.sim_button import SimButton
        from simulation.sim_display import SimDisplay

        mic = SimMicrophone(sample_rate=sample_rate, channels=channels,
                            chunk_size=chunk_size)
        spk = SimSpeaker()
        btn = SimButton()
        logger.info("  ✓ Microphone: SimMicrophone")
        logger.info("  ✓ Speaker:    SimSpeaker")
        logger.info("  ✓ Button:     SimButton")

        display = None
        if enable_display:
            display = SimDisplay()
            display.init()
            logger.info("  ✓ Display:    SimDisplay")

        return HardwareKit(
            microphone=mic, speaker=spk, button=btn,
            display=display, camera=None, platform=platform,
        )
