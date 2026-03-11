import numpy as np
import seabreeze as sb
import logging

class OceanOpticsSpectrometer:

    """
    Controlador para Espectrofotómetro Ocean Optics compatible con IvoryOS.
    """
    def __init__(self, integration_time_micros: int = 100000, num_scans: int = 5):
        self.integration_time = integration_time_micros
        self.num_scans = num_scans
        
        try:
            # 1. Busca los aparatos conectados por USB
            devices = sb.list_devices()
            if not devices:
                raise Exception("No se ha encontrado ningun espectrofotometro conectado!")

            # 2. Conecta con el primer aparato que encuentre
            self.spectrometer = sb.Spectrometer(devices[0])
            
            # 3. Le aplica la configuracion
            self.spectrometer.integration_time_micros(self.integration_time)
            
            logging.info("ESPECTROFOTOMETRO - Conectado con exito")
        except Exception as e:
            logging.error(f"ESPECTROFOTOMETRO - Fallo al conectar: {str(e)}")
            raise

    def close_connection(self):
        """Cierra la comunicacion con el aparato."""
        try:
            self.spectrometer.close()
            logging.info("Conexion cerrada correctamente.")
        except Exception as e:
            logging.error(f"Fallo al cerrar la conexion: {str(e)}")
            raise