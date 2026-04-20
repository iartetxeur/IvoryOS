"""
IvoryOS - Punto de entrada principal
=====================================
Uso:
    python -m ivoryos.main                  → menú interactivo para elegir deck
    python -m ivoryos.main sintesis         → lanza directamente el deck de síntesis
    python -m ivoryos.main analisis         → lanza directamente el deck de análisis
    python -m ivoryos.main todo             → lanza todos los instrumentos
    python -m ivoryos.main simulacion       → lanza en modo offline (sin hardware)
"""
import sys
import importlib
import ivoryos


# =============================================================
# CONFIGURACIÓN DE DECKS DISPONIBLES
# Para añadir un nuevo deck: crea ivoryos/decks/deck_NOMBRE.py
# y añade una entrada aquí.
# =============================================================
DECKS = {
    "1": {
        "nombre": "sintesis",
        "descripcion": "Síntesis      — Bombas, IKA, Espectrómetro",
    },
    "2": {
        "nombre": "analisis",
        "descripcion": "Análisis      — Espectrómetro Ocean Optics",
    },
    "3": {
        "nombre": "todo",
        "descripcion": "Todo          — Todo el hardware del laboratorio",
    },
    "4": {
        "nombre": "simulacion",
        "descripcion": "Simulación    — Sin hardware real (para programar en casa)",
    },
}

_NOMBRES_VALIDOS = {info["nombre"] for info in DECKS.values()}


# =============================================================
# SELECCIÓN DEL DECK
# =============================================================
def _seleccionar_deck() -> str:
    """
    Devuelve el nombre del deck a cargar.
    Prioridad: argumento de consola > menú interactivo.
    """
    # --- Argumento por línea de comandos ---
    if len(sys.argv) > 1:
        arg = sys.argv[-1].lower()
        if arg in _NOMBRES_VALIDOS:
            print(f"\n[INFO] Deck seleccionado por argumento: '{arg}'")
            return arg
        else:
            print(f"\n[AVISO] Argumento '{arg}' no reconocido. "
                  f"Opciones válidas: {', '.join(sorted(_NOMBRES_VALIDOS))}")

    # --- Menú interactivo ---
    ancho = 58
    print("\n" + "=" * ancho)
    print("IVORYOS  —  ¿Qué deck quieres arrancar?")
    print("=" * ancho)
    for num, info in DECKS.items():
        print(f"   [{num}]  {info['descripcion']}")
    print("=" * ancho)

    while True:
        try:
            eleccion = input("\n   Introduce el número (1–4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n[INFO] Cancelado por el usuario.")
            sys.exit(0)

        if eleccion in DECKS:
            return DECKS[eleccion]["nombre"]

        print("   ❌  Opción no válida. Elige entre 1 y 4.")


# =============================================================
# CARGA DEL DECK SELECCIONADO
# =============================================================
deck_seleccionado = _seleccionar_deck()

print(f"\n{'=' * 58}")
print(f"INICIALIZANDO DECK: {deck_seleccionado.upper()}")
print(f"{'=' * 58}\n")

# Importar el módulo del deck dinámicamente
_deck_module = importlib.import_module(f"ivoryos.decks.deck_{deck_seleccionado}")

# Inyectar el hardware del deck en el namespace de ESTE módulo (__main__)
# Esto es imprescindible para que ivoryos.run(__name__) encuentre los
# objetos de hardware a través de sys.modules["__main__"].
for _nombre_hw in getattr(_deck_module, "__all__", []):
    globals()[_nombre_hw] = getattr(_deck_module, _nombre_hw)


# =============================================================
# ARRANQUE DEL SERVIDOR
# =============================================================
if __name__ == "__main__":
    try:
        ivoryos.run(__name__, debug=False)

    except KeyboardInterrupt:
        print("\n\n[INFO] Deteniendo el servidor por Ctrl+C...")

    finally:
        print("\n[INFO] Cerrando conexiones de hardware de forma segura...")
        _hardware_list = getattr(_deck_module, "HARDWARE_OBJECTS", [])
        for _hw in _hardware_list:
            if _hw is None:
                continue
            try:
                conn = getattr(_hw, "connection", None)
                if conn and getattr(conn, "is_open", False):
                    conn.close()
                    print(f"   ✅ Puerto COM liberado: {type(_hw).__name__}")
            except Exception as e:
                print(f"   ⚠️  Error cerrando {type(_hw).__name__}: {e}")

        print("\n[INFO] Sistema apagado correctamente.")
        sys.exit(0)
