# =============================================================
# DECK: TODO EL HARDWARE
# Carga todo el hardware disponible en el laboratorio.
# Este archivo es importado dinamicamente por main.py.
# NO ejecutar directamente.
# =============================================================

from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer
from ivoryos.hardware.chopper.thorlabs_chopper import ThorlabsChopper
from ivoryos.hardware.pico.g2v_pico import G2VPicoLight
from ivoryos.hardware.laser.obis_laser import ObisLaser
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer
from ivoryos.decks.hw_config import (
    PUMP_1_COM, PUMP_2_COM, IKA_COM,
    CHOPPER_COM, LASER_COM, G2V_IP, G2V_ID,
    SPEC_INTEGRATION_TIME, SPEC_NUM_SCANS,
    _safe_init
)

print("[INFO] Cargando TODO el hardware disponible...")

pump_1                    = _safe_init(IsmatecPump,             port=PUMP_1_COM)
pump_2                    = _safe_init(IsmatecPump,             port=PUMP_2_COM)
ika_stirrer               = _safe_init(IkaStirrer,              port=IKA_COM)
chopper_optico            = _safe_init(ThorlabsChopper,         port=CHOPPER_COM)
g2v_pico_light            = _safe_init(G2VPicoLight,            ip_address=G2V_IP, pico_id=G2V_ID)
obis_laser                = _safe_init(ObisLaser,               port=LASER_COM)
ocean_optics_spectrometer = _safe_init(OceanOpticsSpectrometer, integration_time_micros=SPEC_INTEGRATION_TIME, num_scans=SPEC_NUM_SCANS)

print("[INFO] Hardware cargado.")

HARDWARE_OBJECTS = [obj for obj in [pump_1, pump_2, ika_stirrer, chopper_optico, g2v_pico_light, obis_laser] if obj is not None]

__all__ = [
    "pump_1",
    "pump_2",
    "ika_stirrer",
    "chopper_optico",
    "g2v_pico_light",
    "obis_laser",
    "ocean_optics_spectrometer",
    "HARDWARE_OBJECTS",
]
