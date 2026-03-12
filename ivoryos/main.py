import ivoryos
from hardware.ocean_optics_spectrometer import OceanOpticsSpectrometer 

# Al crear el objeto aquí, Python buscará físicamente el hardware por USB.
ocean_optics_spectrometer = OceanOpticsSpectrometer(
    integration_time_micros=100000, 
    num_scans=5
)

if __name__ == "__main__":
    # Arranca la interfaz web con el hardware ya conectado
    ivoryos.run(__name__)