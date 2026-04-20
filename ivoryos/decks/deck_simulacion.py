# =============================================================
# DECK: SIMULACIÓN
# Deck vacío para programar y probar scripts sin hardware real.
# Perfecto para trabajar desde casa o sin el laboratorio conectado.
# Este archivo es importado dinámicamente por main.py.
# NO ejecutar directamente.
# =============================================================

print("[INFO] Modo Simulación activo - No se inicia ningún hardware real.")
print("[INFO] Todos los instrumentos estarán en modo offline (None).")

# ------------------------------------------------------------------
# HARDWARE_OBJECTS: vacío porque no hay hardware que cerrar
# ------------------------------------------------------------------
HARDWARE_OBJECTS = []

# ------------------------------------------------------------------
# __all__: vacío en modo simulación. Puedes añadir variables mock
# aquí si necesitas probar el comportamiento de la interfaz.
# ------------------------------------------------------------------
__all__ = [
    "HARDWARE_OBJECTS",
]
