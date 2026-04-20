# =============================================================
# DECK: ANALISIS DE TEMPERATURA
# IKA RCT 5 con registro automatico de temperatura.
# El log arranca solo al encender calefaccion/motor
# y guarda CSV + grafica PNG al apagarlos.
# NO ejecutar directamente.
# =============================================================

from ivoryos.hardware.stirrer.temperature_logger import IkaStirrerWithLogging
from ivoryos.decks.hw_config import IKA_COM

print("[INFO] Cargando hardware de Analisis de Temperatura...")

try:
    ika_stirrer = IkaStirrerWithLogging(port=IKA_COM, interval_seconds=30)
except Exception as e:
    print(f"IKA Stirrer no disponible en {IKA_COM}: {e}")
    ika_stirrer = None

print("[INFO] Hardware de Analisis de Temperatura cargado.")

HARDWARE_OBJECTS = [obj for obj in [ika_stirrer] if obj is not None]

__all__ = [
    "ika_stirrer",
    "HARDWARE_OBJECTS",
]
