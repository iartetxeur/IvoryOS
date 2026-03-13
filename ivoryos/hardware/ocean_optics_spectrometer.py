import numpy as np
import seabreeze.spectrometers as sb
import logging
import seabreeze
seabreeze.use('pyseabreeze')
import matplotlib.pyplot as plt
import os
import time

class OceanOpticsSpectrometer:
    """
    Controlador para Espectrofotómetro Ocean Optics.
    """

    def __init__(self, integration_time_micros: int = 100000, num_scans: int = 5):
        """
        Inicializa la conexión real con el hardware por USB.
        :param integration_time_micros: Tiempo de integración.
        :param num_scans: Número de mediciones a promediar.
        """
        self.integration_time = integration_time_micros
        self.num_scans = num_scans
        
        try:
            # 1. Busca el hardware conectado
            devices = sb.list_devices()
            if not devices:
                raise Exception("¡No se ha encontrado ningún espectrofotómetro conectado!")

            # 2. Conecta y aplica configuración
            self.spectrometer = sb.Spectrometer(devices[0])
            self.spectrometer.integration_time_micros(self.integration_time)
            
            # Guardamos las longitudes de onda (como lista para evitar errores de IvoryOS)
            self.wavelengths = self.spectrometer.wavelengths().tolist()
            
            self.baseline = None
            self.dark_spectrum = None

            logging.info("SPECTROMETER - Conectado con éxito al hardware real")
        except Exception as e:
            logging.error(f"Fallo al conectar con el equipo: {str(e)}")
            raise

    def average_scans(self) -> list:
        """Toma múltiples mediciones y devuelve la media."""
        logging.info(f"Tomando {self.num_scans} medidas para promediar...")
        scans = [self.spectrometer.intensities() for _ in range(self.num_scans)]
        # Convertimos la salida de numpy a lista estándar de Python
        return np.mean(scans, axis=0).tolist()

    def take_baseline(self) -> list:
        """
        Toma la medida de referencia (baseline) con la lámpara encendida y el blanco.
        """
        logging.info("Grabando línea base (baseline)...")
        self.baseline = self.average_scans()
        logging.info("Línea base guardada.")
        return self.baseline

    def take_dark_spectrum(self) -> list:
        """
        Toma el espectro oscuro. 
        IMPORTANTE: Apaga la lámpara ANTES de que IvoryOS ejecute este paso.
        """
        logging.info("Grabando espectro oscuro (dark spectrum)...")
        self.dark_spectrum = self.average_scans()
        logging.info("Espectro oscuro guardado.")
        return self.dark_spectrum

    def take_current_spectrum(self) -> list:
        """Mide el espectro de la muestra actual de la reacción."""
        logging.info("Midiendo muestra actual...")
        current_spectrum = self.spectrometer.intensities().tolist()
        try:
      # 2. Dibujar
            plt.figure(figsize=(10, 5))
            plt.plot(current_spectrum, color='blue')
            plt.title(f'Espectro - {time.strftime("%H:%M:%S")}')
            plt.grid(True)
            
            # 3. Guardar con nombre único
            nombre_archivo = f"espectro_{time.strftime('%H%M%S')}.png"
            ruta_imagen = os.path.join(os.getcwd(), nombre_archivo)
            
            plt.savefig(ruta_imagen)
            plt.close('all') # Cerramos todo para liberar memoria
            print(f"---> FOTO GUARDADA: {nombre_archivo}")
        except Exception as e:
            print(f"No se pudo dibujar la gráfica: {e}")


        return current_spectrum
    def close_connection(self):
        """Cierra la conexión USB de forma segura."""
        self.spectrometer.close()
        logging.info("Conexión con el espectrofotómetro cerrada correctamente.")