# =============================================================
# DECK: SINTESIS
# Hardware para el reactor de sintesis de nanoparticulas.
# Este archivo es importado dinamicamente por main.py.
# NO ejecutar directamente.
# =============================================================

from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer
from ivoryos.decks.hw_config import (
    PUMP_1_COM, PUMP_2_COM, IKA_COM,
    SPEC_INTEGRATION_TIME, SPEC_NUM_SCANS,
    _safe_init
)

print("[INFO] Cargando hardware de Sintesis...")

pump_1                    = _safe_init(IsmatecPump,             port=PUMP_1_COM)
pump_2                    = _safe_init(IsmatecPump,             port=PUMP_2_COM)
ocean_optics_spectrometer = _safe_init(OceanOpticsSpectrometer, integration_time_micros=SPEC_INTEGRATION_TIME, num_scans=SPEC_NUM_SCANS)

# IKA se inicializa directamente (sin hilo daemon) para que pyserial
# funcione correctamente desde los hilos de Flask en Windows
try:
    ika_stirrer = IkaStirrer(port=IKA_COM)
except Exception as e:
    print(f"IKA Stirrer no disponible en {IKA_COM}: {e}")
    ika_stirrer = None

print("[INFO] Hardware de Sintesis cargado.")

HARDWARE_OBJECTS = [obj for obj in [pump_1, pump_2, ika_stirrer] if obj is not None]

__all__ = [
    "pump_1",
    "pump_2",
    "ika_stirrer",
    "ocean_optics_spectrometer",
    "HARDWARE_OBJECTS",
]
