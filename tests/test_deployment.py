"""Static checks for Pi deployment artifacts that run on any dev OS."""

import configparser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pi_simulation_requirements_omit_hardware_audio_packages():
    requirement_lines = (
        ROOT / "deployment" / "requirements-pi-simulation.txt"
    ).read_text(encoding="utf-8").lower().splitlines()
    packages = [
        line.partition("#")[0].strip()
        for line in requirement_lines
        if line.partition("#")[0].strip()
    ]

    assert any(line.startswith("groq") for line in packages)
    assert any(line.startswith("python-dotenv") for line in packages)
    assert any(line.startswith("pytest") for line in packages)
    assert not any("pyaudio" in line for line in packages)
    assert not any("portaudio" in line for line in packages)


def test_armv6_constraint_avoids_pydantic_core_profile():
    constraint_lines = (
        ROOT / "deployment" / "armv6-constraints.txt"
    ).read_text(encoding="utf-8").lower().splitlines()
    constraints = [
        line.partition("#")[0].strip()
        for line in constraint_lines
        if line.partition("#")[0].strip()
    ]

    assert "pydantic<2" in constraints
    assert not any("pydantic-core" in line for line in constraints)


def test_systemd_template_is_manual_first_and_secret_free():
    unit_path = ROOT / "deployment" / "vihaan.service"
    unit_text = unit_path.read_text(encoding="utf-8")
    unit = configparser.ConfigParser(interpolation=None)
    unit.read_string(unit_text)

    assert unit["Service"]["User"] == "vihaan"
    assert unit["Service"]["Group"] == "vihaan"
    assert unit["Service"]["EnvironmentFile"] == "/etc/vihaan/vihaan.env"
    assert unit["Service"]["Restart"] == "on-failure"
    assert unit["Service"]["RestartSec"] == "10"
    assert "GROQ_API_KEY=" not in unit_text
    assert "systemctl enable" not in unit_text
