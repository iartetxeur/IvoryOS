import numpy as np
import seabreeze.spectrometers as sb
import logging
import seabreeze
seabreeze.use('pyseabreeze')

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

import os
import time
import csv

class OceanOpticsSpectrometer:
    def __init__(self, integration_time_micros: int = 100000, num_scans: int = 5):
        self.integration_time = integration_time_micros
        self.num_scans = num_scans
        self.spectrometer = None  
        self.wavelengths = []
        
        try:
            devices = sb.list_devices()
            if devices:
                self.spectrometer = sb.Spectrometer(devices[0])
                self.spectrometer.integration_time_micros(self.integration_time)
                self.wavelengths = self.spectrometer.wavelengths().tolist()
                print("✅ Espectrómetro Ocean Optics detectado y listo.")
            else:
                raise Exception("No devices found")
                
        except Exception:
            print("❌ AVISO: Espectrómetro Ocean Optics NO detectado. Trabajando en modo offline.")

    def _get_target_dir(self):
        """Busca automáticamente la carpeta del experimento que IvoryOS acaba de crear."""
        base_dir = os.path.join(os.getcwd(), 'ivoryos_data', 'results')
        os.makedirs(base_dir, exist_ok=True)
        # Filtra para encontrar la subcarpeta más reciente dentro de results
        carpetas = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        return max(carpetas, key=os.path.getmtime) if carpetas else base_dir

    def _save_data(self, intensities, prefix, integration_time_micros, num_scans):
        """Crea la gráfica PNG y el CSV con el prefijo DATA_ para que la web lo muestre."""
        if not intensities:
            return
            
        target_dir = self._get_target_dir()
        file_time = time.strftime('%H-%M-%S')
        
        # 1. Crear y guardar gráfica
        plt.figure(figsize=(10, 5))
        plt.plot(self.wavelengths, intensities, color='blue')
        plt.title(f'{prefix} - {file_time}')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity')
        plt.grid(True)
        plt.savefig(os.path.join(target_dir, f"{prefix.lower()}_{file_time}.png"))
        plt.close('all')

        # 2. Guardar CSV (Solo este aparecerá en la pestaña DATA gracias al filtro de execute.py)
        csv_path = os.path.join(target_dir, f"DATA_{prefix}_{file_time}.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Wavelength (nm)', 'Intensity'])
            for w, i in zip(self.wavelengths, intensities):
                writer.writerow([w, i])

    def take_baseline(self, integration_time_micros: int = 100000, num_scans: int = 5):
        """Mide el blanco. Solo funciona si el USB está conectado."""
        if self.spectrometer:
            self.spectrometer.integration_time_micros(integration_time_micros)
            scans = [self.spectrometer.intensities() for _ in range(num_scans)]
            data = np.mean(scans, axis=0).tolist()
            self._save_data(data, "BASELINE", integration_time_micros, num_scans)
            return data
        return None

    def take_dark_spectrum(self, integration_time_micros: int = 100000, num_scans: int = 5):
        """Mide el espectro oscuro. Solo funciona si el USB está conectado."""
        if self.spectrometer:
            self.spectrometer.integration_time_micros(integration_time_micros)
            scans = [self.spectrometer.intensities() for _ in range(num_scans)]
            data = np.mean(scans, axis=0).tolist()
            self._save_data(data, "DARK", integration_time_micros, num_scans)
            return data
        return None

    def take_current_spectrum(self, integration_time_micros: int = 100000, num_scans: int = 5):
        if self.spectrometer:
            self.spectrometer.integration_time_micros(integration_time_micros)
            scans = [self.spectrometer.intensities() for _ in range(num_scans)]
            data = np.mean(scans, axis=0).tolist()
            self._save_data(data, "SAMPLE", integration_time_micros, num_scans)
            return data
        return None

    def close_connection(self):
        """Cierra la comunicación USB si estaba abierta."""
        if self.spectrometer:
            self.spectrometer.close()