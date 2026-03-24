import ivoryos
import logging
import sys

# Importamos los drivers de nuestros equipos
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 
from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer

# ==========================================
# --- CONFIGURACIÓN DE HARDWARE ---
# ==========================================

# 1. OCEAN OPTICS SPECTROMETER
ocean_optics_spectrometer = OceanOpticsSpectrometer(
    integration_time_micros=100000, 
    num_scans=5
)

# 2. ISMATEC PUMPS
# Al estar en USBs independientes (HUB), cada una es la dueña de su cable,
# por lo que no hace falta usar 'address'.
pump_1 = IsmatecPump(port="COM8")
pump_2 = IsmatecPump(port="COM9")

# 3. IKA STIRRER
# Conectado en el puerto COM5 (con lectura de temperatura y RPM)
ika_stirrer = IkaStirrer(port="COM5")

# ==========================================
# --- ARRANQUE DEL SERVIDOR ---
# ==========================================

if __name__ == "__main__":
    try:
        # Arranca la interfaz web de IvoryOS. 
        # debug=False evita que el servidor arranque dos veces y oculte los mensajes de la consola.
        ivoryos.run(__name__, debug=False)
        
    except KeyboardInterrupt:
        # Esto captura cuando pulsas Ctrl+C en la consola
        print("\n[INFO] Deteniendo servidores por el usuario (Ctrl+C)...")
        
    finally:
        # CIERRE SEGURO DE PUERTOS: Evita errores de "NoneType" o bloqueos en los COM
        print("[INFO] Cerrando conexiones de hardware...")
        
        # Cerramos Bomba 1 y 2 comprobando si existen
        for pump_name in ['pump_1', 'pump_2']:
            if pump_name in locals():
                p = locals()[pump_name]
                if hasattr(p, 'connection') and p.connection:
                    p.connection.close()
                    print(f" - {pump_name} cerrada de forma segura.")
        
        # Cerramos Agitador
        if 'ika_stirrer' in locals() and hasattr(ika_stirrer, 'connection') and ika_stirrer.connection:
            ika_stirrer.connection.close()
            print(" - Agitador IKA cerrado de forma segura.")
            
            
        print("✅ Todos los puertos COM han sido liberados. Servidor detenido.")
        sys.exit(0)