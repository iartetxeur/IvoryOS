import sys
import ivoryos

from ivoryos.hardware.pump.ismatec_pump import IsmatecPump
from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer
from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 
from ivoryos.hardware.chopper.thorlabs_chopper import ThorlabsChopper
from ivoryos.hardware.pico.g2v_pico import G2VPicoLight
from ivoryos.hardware.laser.obis_laser import ObisLaser



print("🚀 INICIALIZANDO DECK: SÍNTESIS")

# Guardamos los instrumentos
pump_1 = IsmatecPump(port="COM8")
pump_2 = IsmatecPump(port="COM9")
ika_stirrer = IkaStirrer(port="COM5")
ocean_optics_spectrometer = OceanOpticsSpectrometer()
thorlabs_chopper = ThorlabsChopper(port="COM13")
g2v_pico_light = G2VPicoLight(ip_address="", pico_id="")
obis_laser = None # ObisLaser(port="COM7")


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
        if hasattr(thorlabs_chopper, 'connection') and thorlabs_chopper.connection: thorlabs_chopper.connection.close()
        if hasattr(g2v_pico_light, 'connection') and g2v_pico_light.connection: g2v_pico_light.connection.close()
        if hasattr(obis_laser, 'connection') and obis_laser.connection: obis_laser.connection.close()
        if 'ocean_optics_spectrometer' in locals():
            del ocean_optics_spectrometer 
        sys.exit(0)