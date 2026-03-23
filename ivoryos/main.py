import ivoryos
import logging
import sys

from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 
from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer

# 1. OCEAN OPTICS SPECTROMETER
ocean_optics_spectrometer = OceanOpticsSpectrometer(
    integration_time_micros=100000, 
    num_scans=5
)

# 2. ISMATEC PUMPS
pump_1 = IsmatecPump(port="COM8", address=1)
pump_2 = IsmatecPump(port="COM8", address=2)

# 3. IKA STIRRER (Con funciones de lectura de temperatura y RPM)
ika_stirrer = IkaStirrer(port="COM9")

if __name__ == "__main__":
    try:
        # Arranca la interfaz web de IvoryOS
        ivoryos.run(__name__)
        
    except KeyboardInterrupt:
        print("\n[INFO] Deteniendo servidores por el usuario (Ctrl+C)...")
        
    finally:
        # CIERRE SEGURO DE PUERTOS: Evita errores de "NoneType" o "Device not recognized"
        print("[INFO] Cerrando conexiones de hardware...")
        
        # Cerramos Bomba 1 y 2
        for p in [pump_1, pump_2]:
            if hasattr(p, 'connection') and p.connection:
                p.connection.close()
        
        # Cerramos Agitador
        if hasattr(ika_stirrer, 'connection') and ika_stirrer.connection:
            ika_stirrer.connection.close()
            
        print("✅ Todos los puertos COM han sido liberados. Servidor detenido.")
        sys.exit(0)