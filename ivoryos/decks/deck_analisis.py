# =============================================================
# DECK: ANALISIS OPTICO
# Hardware para medidas espectroscopicas.
# Este archivo es importado dinamicamente por main.py.
# NO ejecutar directamente.
# =============================================================

from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer
from ivoryos.decks.hw_config import SPEC_INTEGRATION_TIME, SPEC_NUM_SCANS

print("[INFO] Cargando hardware de Analisis Optico...")

ocean_optics_spectrometer = OceanOpticsSpectrometer(
    integration_time_micros=SPEC_INTEGRATION_TIME,
    num_scans=SPEC_NUM_SCANS
)
# chopper_optico = ThorlabsChopper(port=CHOPPER_COM)  # Descomentar cuando lo uses

# ------------------------------------------------------------------
# HARDWARE_OBJECTS
# ------------------------------------------------------------------
HARDWARE_OBJECTS = []  # El espectrometro Ocean Optics no usa puerto serial clasico

# ------------------------------------------------------------------
# __all__
# ------------------------------------------------------------------
__all__ = [
    "ocean_optics_spectrometer",
    "HARDWARE_OBJECTS",
]
