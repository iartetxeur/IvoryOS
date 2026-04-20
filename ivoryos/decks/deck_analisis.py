# =============================================================
# DECK: ANÁLISIS ÓPTICO
# Hardware para medidas espectroscópicas.
# Este archivo es importado dinámicamente por main.py.
# NO ejecutar directamente.
# =============================================================

from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer

print("[INFO] Cargando hardware de Análisis Óptico...")

ocean_optics_spectrometer = OceanOpticsSpectrometer(integration_time_micros=100000, num_scans=5)
# chopper_optico = ThorlabsChopper(port="COM10")  # Descomentar cuando lo uses

# ------------------------------------------------------------------
# HARDWARE_OBJECTS: lista usada por main.py para cerrar los puertos
# al apagar el servidor.
# ------------------------------------------------------------------
HARDWARE_OBJECTS = []  # El espectrómetro Ocean Optics no usa puerto serial clásico

# ------------------------------------------------------------------
# __all__: variables que se inyectarán en el namespace de main.py
# ------------------------------------------------------------------
__all__ = [
    "ocean_optics_spectrometer",
    "HARDWARE_OBJECTS",
]
