import ivoryos
import logging

from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer 
from ivoryos.hardware.pump.ismatec_pump import IsmatecPump

# Inicializamos el espectrómetro
ocean_optics_spectrometer = OceanOpticsSpectrometer(
    integration_time_micros=100000, 
    num_scans=5
)

pump_ismatec = IsmatecPump(port="COM7")

if __name__ == "__main__":
    try:
        # Arranca la interfaz web
        ivoryos.run(__name__)
    except KeyboardInterrupt:
        # Esto soluciona el problema de que tarde mucho en cerrarse
        print("\nCerrando conexiones...")
        if 'pump_ismatec' in globals() and pump_ismatec.connection:
            pump_ismatec.connection.close()
        print("Servidor detenido.")