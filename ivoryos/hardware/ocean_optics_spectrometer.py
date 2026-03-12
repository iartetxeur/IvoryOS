import numpy as np
import seabreeze.spectrometers as sb
import logging
import seabreeze
seabreeze.use('pyseabreeze') 
import matplotlib.pyplot as plt
import os
import time

# Intentamos importar la API de OceanDirect para el control de la lámpara
try:
    from .OceanDirectAPI import OceanDirectAPI
    OD_AVAILABLE = True
except ImportError:
    OD_AVAILABLE = False
    print("AVISO: No se encontró OceanDirectAPI.py en la carpeta. La lámpara podría no encender.")

class OceanOpticsSpectrometer:
    def __init__(self, integration_time_micros: int = 100000, num_scans: int = 5):
        self.integration_time = integration_time_micros
        self.num_scans = num_scans
        self.spectrometer = None
        self.od_device = None
        
        try:
            # 1. Conexión SeaBreeze (para datos)
            devices = sb.list_devices()
            if devices:
                self.spectrometer = sb.Spectrometer(devices[0])
                self.spectrometer.integration_time_micros(self.integration_time)
                self.wavelengths = self.spectrometer.wavelengths().tolist()

            # 2. Conexión OceanDirect (solo para la Lámpara)
            if OD_AVAILABLE:
                self.api = OceanDirectAPI()
                device_ids = self.api.get_device_ids()
                if device_ids:
                    self.od_device = self.api.open_device(device_ids[0])
                    print("API OceanDirect vinculada para control de lámpara.")

            logging.info("Conexión dual establecida (SeaBreeze + OceanDirect)")
        except Exception as e:
            logging.error(f"Error en inicialización: {e}")

    def take_current_spectrum(self) -> list:
        """Mide y guarda la gráfica como antes."""
        intensities = self.spectrometer.intensities()
        try:
            plt.figure(figsize=(10, 5))
            plt.plot(self.wavelengths, intensities, color='blue')
            plt.title(f'Espectro - {time.strftime("%H:%M:%S")}')
            plt.savefig(f"espectro_{time.strftime('%H%M%S')}.png")
            plt.close('all')
        except: pass
        return intensities.tolist()

    def set_lamp_halogen(self, state: bool):
        """Control total usando OceanDirect para Pins 5 y 13."""
        if not self.od_device:
            print("Error: El hardware de la lámpara no está disponible vía OceanDirect.")
            return

        try:
            # Máscara: Pin 5 (bit 4) y Pin 13 (bit 12)
            mask = (1 << 4) | (1 << 12)
            
            # Configuramos los pines como salida (output)
            self.od_device.set_gpio_output_enable_mask(mask)
            
            if state:
                # Ponemos los pines en ALTO (5V)
                self.od_device.set_gpio_value_mask(mask)
                print("--- [OceanDirect] Halógena y Shutter: ACTIVADOS ---")
            else:
                self.od_device.set_gpio_value_mask(0)
                print("--- [OceanDirect] Halógena y Shutter: APAGADOS ---")
        except Exception as e:
            print(f"Error de API OceanDirect: {e}")

    def set_lamp_uv(self, state: bool):
        """Control de Deuterio (Pin 1) vía OceanDirect."""
        if self.od_device:
            mask = 0x01 # Pin 1
            self.od_device.set_gpio_output_enable_mask(mask)
            val = mask if state else 0
            self.od_device.set_gpio_value_mask(val)
            print(f"--- [OceanDirect] Deuterio: {'ON' if state else 'OFF'} ---")

    def average_scans(self) -> list: return [0] # Placeholder
    def take_baseline(self) -> list: return [0] # Placeholder
    def take_dark_spectrum(self) -> list: return [0] # Placeholder
    def close_connection(self):
        if self.spectrometer: self.spectrometer.close()
        if self.od_device: self.od_device.close()