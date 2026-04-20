# =============================================================
# DECK: ANALISIS DE TEMPERATURA
# Solo el agitador IKA para experimentos de temperatura.
# Este archivo es importado dinamicamente por main.py.
# NO ejecutar directamente.
# =============================================================

from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer
from ivoryos.decks.hw_config import IKA_COM

print("[INFO] Cargando hardware de Analisis de Temperatura...")

# IKA se inicializa directamente (sin hilo daemon) para que pyserial
# funcione correctamente desde los hilos de Flask en Windows
try:
    ika_stirrer = IkaStirrer(port=IKA_COM)
except Exception as e:
    print(f"IKA Stirrer no disponible en {IKA_COM}: {e}")
    ika_stirrer = None

print("[INFO] Hardware de Analisis de Temperatura cargado.")

# ------------------------------------------------------------------
# HARDWARE_OBJECTS: para cerrar puertos al apagar
# ------------------------------------------------------------------
HARDWARE_OBJECTS = [obj for obj in [ika_stirrer] if obj is not None]

# ------------------------------------------------------------------
# __all__: variables inyectadas en el namespace de main.py
# ------------------------------------------------------------------
__all__ = [
    "ika_stirrer",
    "HARDWARE_OBJECTS",
]
