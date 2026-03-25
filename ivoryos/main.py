import sys
import logging
import ivoryos

# --- IMPORTACIONES DE HARDWARE ---
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 
from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer

# ==========================================
# --- SISTEMA DE SELECCIÓN DE DECK ---
# ==========================================

# Por defecto, si no le decimos nada al arrancar, cargará el deck "sintesis"
deck_seleccionado = "sintesis"

# Si le pasamos un argumento por consola (ej: python -m ivoryos.main analisis)
if len(sys.argv) > 1:
    # Usamos [-1] para coger el último argumento de forma segura, 
    # por si Python añade argumentos extra como el '-m'
    argumento = sys.argv[-1].lower()
    if argumento in ["sintesis", "analisis", "todo", "simulacion"]:
        deck_seleccionado = argumento

print(f"\n{'='*50}")
print(f"🚀 INICIALIZANDO IVORYOS - DECK: {deck_seleccionado.upper()}")
print(f"{'='*50}\n")

# ==========================================
# --- CONFIGURACIÓN DE LOS DECKS ---
# ==========================================

if deck_seleccionado == "sintesis":
    print("[INFO] Cargando hardware de Síntesis...")
    pump_1 = IsmatecPump(port="COM8")
    pump_2 = IsmatecPump(port="COM9")
    ika_stirrer = IkaStirrer(port="COM5")

elif deck_seleccionado == "analisis":
    print("[INFO] Cargando hardware de Análisis Óptico...")
    ocean_optics_spectrometer = OceanOpticsSpectrometer(integration_time_micros=100000, num_scans=5)
    # chopper_optico = ThorlabsChopper(port="COM10") # Descomentar cuando lo uses

elif deck_seleccionado == "todo":
    print("[INFO] Cargando TODO el hardware disponible...")
    pump_1 = IsmatecPump(port="COM8")
    pump_2 = IsmatecPump(port="COM9")
    ika_stirrer = IkaStirrer(port="COM5")
    ocean_optics_spectrometer = OceanOpticsSpectrometer()

elif deck_seleccionado == "simulacion":
    print("[INFO] Cargando en Modo Simulación (Deck vacío para programar en casa)...")
    pass # No iniciamos ningún hardware real

# ==========================================
# --- ARRANQUE DEL SERVIDOR ---
# ==========================================

if __name__ == "__main__":
    try:
        # Arranca la web. ¡El modo Debug apagado para no silenciar los errores!
        ivoryos.run(__name__, debug=False)
        
    except KeyboardInterrupt:
        print("\n[INFO] Deteniendo el servidor por el usuario (Ctrl+C)...")
        
    finally:
        print("\n[INFO] Cerrando conexiones de hardware de forma segura...")
        
        # Bucle inteligente que busca cualquier hardware que se haya abierto y cierra su puerto
        for obj_name, obj in list(locals().items()):
            if hasattr(obj, 'connection') and obj.connection:
                if hasattr(obj.connection, 'is_open') and obj.connection.is_open:
                    try:
                        obj.connection.close()
                        print(f" ✅ Puerto COM liberado para: {obj_name}")
                    except Exception as e:
                        print(f" ⚠️ Error cerrando {obj_name}: {e}")
                        
        print("👋 Sistema apagado correctamente.")
        sys.exit(0)