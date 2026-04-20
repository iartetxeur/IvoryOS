"""
hw_config.py - Configuracion centralizada de hardware
======================================================
Lee el archivo .env de la raiz del proyecto y expone
los valores como constantes para todos los decks.

Para cambiar un puerto COM: edita el .env, no este archivo.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raiz del proyecto (dos niveles arriba de este archivo)
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()

# --- Bombas ---
PUMP_1_COM  = _get("PUMP_1_COM",  "COM10")
PUMP_2_COM  = _get("PUMP_2_COM",  "COM12")

# --- Agitador IKA ---
IKA_COM     = _get("IKA_COM",     "COM11")

# --- Chopper Thorlabs ---
CHOPPER_COM = _get("CHOPPER_COM", "COM6")

# --- Laser OBIS ---
LASER_COM   = _get("LASER_COM",   "COM7")

# --- Luz G2V Pico ---
G2V_IP      = _get("G2V_IP",      "")
G2V_ID      = _get("G2V_ID",      "")

# --- Espectrometro Ocean Optics ---
SPEC_INTEGRATION_TIME = int(_get("SPEC_INTEGRATION_TIME", "100000"))
SPEC_NUM_SCANS        = int(_get("SPEC_NUM_SCANS",        "5"))


def _safe_init(clase, *args, timeout_s=8.0, **kwargs):
    """
    Inicializa un objeto de hardware en un hilo separado con timeout.
    Si tarda mas de timeout_s segundos, devuelve None y continua.
    """
    import threading
    resultado = [None]

    def _init():
        try:
            resultado[0] = clase(*args, **kwargs)
        except Exception:
            pass

    hilo = threading.Thread(target=_init, daemon=True)
    hilo.start()
    hilo.join(timeout=timeout_s)

    if hilo.is_alive():
        nombre = getattr(clase, "__name__", str(clase))
        print(f"TIMEOUT ({timeout_s}s): {nombre} no responde - continuando en Modo Offline.")

    return resultado[0]
