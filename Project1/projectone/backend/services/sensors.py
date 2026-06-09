"""
Reads the armrest + seat pressure sensors. Same stub/real pattern as the alert
dispatcher: on the laptop there are no sensors, so the stub returns None values
and the rest of the system carries on (your DB columns are nullable, which is
why "no sensor" is a valid reading rather than an error).
"""

from __future__ import annotations


class BaseSensors:
    def read(self) -> dict:
        """Return {'left_armrest': float|None, 'right_armrest': float|None, 'seat': float|None}."""
        raise NotImplementedError

    def cleanup(self) -> None:
        pass


class StubSensors(BaseSensors):
    """Laptop/dev: no hardware, so everything reads as None."""

    def read(self) -> dict:
        return {"left_armrest": None, "right_armrest": None, "seat": None}


class PiSensors(BaseSensors):
    """Raspberry Pi: real ADC reads. Filled in at step 5."""

    def __init__(self):
        # TODO: init the ADC / GPIO channels for the pressure sensors.
        ...

    def read(self) -> dict:
        # TODO: read each channel and return real floats.
        return {"left_armrest": None, "right_armrest": None, "seat": None}


def _on_raspberry_pi() -> bool:
    try:
        with open("/proc/device-tree/model", encoding="utf-8") as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False


def get_sensors() -> BaseSensors:
    if _on_raspberry_pi():
        try:
            return PiSensors()
        except Exception as exc:  # noqa: BLE001
            print(f"[sensors] init failed ({exc}); falling back to stub.")
    return StubSensors()
