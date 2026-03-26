import sys
import ivoryos

from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 

print("🚀 INICIALIZANDO DECK: SÍNTESIS")

# Guardamos los instrumentos
pump_1 = IsmatecPump(port="COM8")
pump_2 = IsmatecPump(port="COM9")
ika_stirrer = IkaStirrer(port="COM5")
ocean_optics_spectrometer = OceanOpticsSpectrometer()

if __name__ == "__main__":
    try:
        ivoryos.run(__name__, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[INFO] Cerrando puertos del Deck de Síntesis...")
        if hasattr(pump_1, 'connection') and pump_1.connection: pump_1.connection.close()
        if hasattr(pump_2, 'connection') and pump_2.connection: pump_2.connection.close()
        if hasattr(ika_stirrer, 'connection') and ika_stirrer.connection: ika_stirrer.connection.close()
        if 'ocean_optics_spectrometer' in locals():
            del ocean_optics_spectrometer 
        sys.exit(0)