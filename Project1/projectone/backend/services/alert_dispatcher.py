"""
Fires the physical feedback (buzzer / LED / OLED). On your Windows laptop there
is no GPIO, so we use a stub that just prints — everything runs without hardware.
On the Pi, the real implementation takes over automatically.

The swap happens once, here, behind get_dispatcher(). Nothing else in the code
needs to know whether it's talking to a real buzzer or a print().
"""

from __future__ import annotations


class BaseDispatcher:
    """Interface every dispatcher implements."""

    def buzz(self, duration_ms: int = 300) -> None:
        raise NotImplementedError

    def led(self, on: bool) -> None:
        raise NotImplementedError

    def oled(self, message: str) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        pass


class StubDispatcher(BaseDispatcher):
    """Laptop/dev: print instead of touching hardware."""

    def buzz(self, duration_ms: int = 300) -> None:
        print(f"[alert:STUB] BUZZER for {duration_ms} ms")

    def led(self, on: bool) -> None:
        print(f"[alert:STUB] LED {'ON' if on else 'OFF'}")

    def oled(self, message: str) -> None:
        print(f"[alert:STUB] OLED: {message}")


class PiDispatcher(BaseDispatcher):
    """
    Raspberry Pi: real GPIO. Filled in when you wire the hardware (step 5).
    Left as a skeleton on purpose so the import doesn't fail on the laptop.
    """

    def __init__(self):
        import RPi.GPIO as GPIO  # noqa: F401  (only available on the Pi)
        # TODO: GPIO.setmode(...), set up buzzer/LED pins, init the OLED.
        self._gpio = GPIO

    def buzz(self, duration_ms: int = 300) -> None:
        # TODO: drive the buzzer pin high for duration_ms, then low.
        ...

    def led(self, on: bool) -> None:
        ...

    def oled(self, message: str) -> None:
        ...

    def cleanup(self) -> None:
        ...


def _on_raspberry_pi() -> bool:
    try:
        with open("/proc/device-tree/model", encoding="utf-8") as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False


def get_dispatcher() -> BaseDispatcher:
    """Return the real dispatcher on a Pi, the stub everywhere else."""
    if _on_raspberry_pi():
        try:
            return PiDispatcher()
        except Exception as exc:  # noqa: BLE001
            print(f"[alert] GPIO init failed ({exc}); falling back to stub.")
    return StubDispatcher()
