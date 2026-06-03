"""Cartridge HAL. Real = I²C EEPROM @0x50 (smbus2) + V+ load-switch PWM (GPIO26).

⚠️ SEQUENCING CONTRACT (carried from Phase 4, electronics.md §4):
   The shared V+ rail powers BOTH the ID EEPROM and the LED ring. LED dimming is done by
   PWM-ing the V+ load switch — which power-cycles the EEPROM. Therefore the core MUST
   read the EEPROM ID FIRST, while V+ is steady, and ONLY THEN start PWM-ing V+ for the LED.
   This ordering is enforced here: enable_power_pwm() raises if read_id() hasn't run.
   A real driver MUST preserve read-before-PWM.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
log = logging.getLogger("vara.cartridge")

EEPROM_ADDR = 0x50  # connector-spec v0.2 §4.1


@dataclass
class CartridgeInfo:
    cartridge_type: int
    hw_rev: int
    name: str
    raw: bytes


class SequencingError(RuntimeError):
    """Raised if V+ PWM is attempted before the EEPROM ID has been read."""


class Cartridge:
    def __init__(self):
        self._id_read = False

    def read_id(self) -> CartridgeInfo | None: raise NotImplementedError
    def _enable_pwm(self, duty: float): raise NotImplementedError

    def enable_power_pwm(self, duty: float = 1.0):
        # The guard that encodes the Phase-4 risk — do not remove.
        if not self._id_read:
            raise SequencingError(
                "V+ PWM attempted before EEPROM read — would corrupt ID read "
                "(read-before-PWM contract, electronics.md §4)")
        self._enable_pwm(duty)


class I2cCartridge(Cartridge):  # REAL — smbus2 + a PWM-capable load-switch enable
    def __init__(self, bus=1, en_gpio=26):
        super().__init__()
        from smbus2 import SMBus  # noqa
        self.SMBus = SMBus; self.bus = bus; self.en_gpio = en_gpio
        log.info("cartridge: REAL I²C EEPROM @0x%02x, V+ EN GPIO%d", EEPROM_ADDR, en_gpio)

    def read_id(self):
        with self.SMBus(self.bus) as b:
            raw = bytes(b.read_byte_data(EEPROM_ADDR, i) for i in range(16))
        self._id_read = True
        return CartridgeInfo(raw[2], raw[3], raw[8:].split(b"\x00")[0].decode("ascii", "ignore"), raw)

    def _enable_pwm(self, duty):
        # real impl: configure hardware PWM on en_gpio at e.g. 1kHz, duty for LED brightness
        log.info("cartridge: V+ PWM duty=%.2f (after ID read)", duty)


class StubCartridge(Cartridge):  # STUB — fake EEPROM record; enforces the ordering in code
    def __init__(self):
        super().__init__()
        log.warning("cartridge: STUB (fake EEPROM @0x%02x — not real I²C)", EEPROM_ADDR)

    def read_id(self):
        self._id_read = True
        rec = CartridgeInfo(cartridge_type=1, hw_rev=1, name="VISION-MACRO",
                            raw=b"VA\x01\x01\x00\x00\x00\x00VISION-MACRO\x00")
        log.info("cartridge[STUB]: id read -> type=%d rev=%d '%s'", rec.cartridge_type, rec.hw_rev, rec.name)
        return rec

    def _enable_pwm(self, duty):
        log.info("cartridge[STUB]: V+ PWM duty=%.2f (correctly AFTER id read)", duty)
