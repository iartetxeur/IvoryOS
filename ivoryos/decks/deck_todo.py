# =============================================================
# DECK: TODO EL HARDWARE
# Carga todo el hardware disponible en el laboratorio.
# Este archivo es importado dinámicamente por main.py.
# NO ejecutar directamente.
# =============================================================

import threading as _threading

from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer
from ivoryos.hardware.chopper.thorlabs_chopper import ThorlabsChopper
from ivoryos.hardware.pico.g2v_pico import G2VPicoLight
from ivoryos.hardware.laser.obis_laser import ObisLaser
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer


def _safe_init(clase, *args, timeout_s=8.0, **kwargs):
    """Inicializa hardware con timeout. Ver deck_sintesis.py para documentación."""
    resultado = [None]

    def _init():
        try:
            resultado[0] = clase(*args, **kwargs)
        except Exception:
            pass

    hilo = _threading.Thread(target=_init, daemon=True)
    hilo.start()
    hilo.join(timeout=timeout_s)

    if hilo.is_alive():
        nombre = getattr(clase, "__name__", str(clase))
        print(f"⏱️  TIMEOUT ({timeout_s}s): {nombre} no responde — continuando en Modo Offline.")

    return resultado[0]


# ------------------------------------------------------------------
# INICIALIZACIÓN DEL HARDWARE
# ------------------------------------------------------------------
print("[INFO] Cargando TODO el hardware disponible...")

pump_1                    = _safe_init(IsmatecPump,              port="COM8")
pump_2                    = _safe_init(IsmatecPump,              port="COM9")
ika_stirrer               = _safe_init(IkaStirrer,               port="COM11")
chopper_optico            = _safe_init(ThorlabsChopper,          port="COM6")
g2v_pico_light            = _safe_init(G2VPicoLight,             ip_address="", pico_id="")
obis_laser                = None  # Descomentar: _safe_init(ObisLaser, port="COM7")
ocean_optics_spectrometer = _safe_init(OceanOpticsSpectrometer,  integration_time_micros=100000, num_scans=5)

print("[INFO] Hardware cargado.")

# ------------------------------------------------------------------
# HARDWARE_OBJECTS
# ------------------------------------------------------------------
HARDWARE_OBJECTS = [obj for obj in [pump_1, pump_2, ika_stirrer, chopper_optico, g2v_pico_light] if obj is not None]

# ------------------------------------------------------------------
# __all__
# ------------------------------------------------------------------
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
