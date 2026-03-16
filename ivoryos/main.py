import ivoryos

from hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 
from hardware.pump.ismatec_pump import IsmatecPump

# Al crear el objeto aquí, Python buscará físicamente el hardware por USB.
ocean_optics_spectrometer = OceanOpticsSpectrometer(
    integration_time_micros=100000, 
    num_scans=5
)

# Inicializamos la bomba con su puerto correspondiente
bomba_ismatec = IsmatecPump(port="COM7")

if __name__ == "__main__":
    # Arranca la interfaz web con el hardware ya conectado
    ivoryos.run(__name__)