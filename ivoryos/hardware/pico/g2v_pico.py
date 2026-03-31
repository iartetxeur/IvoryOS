import logging
import time
import json
import os
from threading import Lock

try:
    from g2vpico import G2VPico
except ImportError:
    G2VPico = None

class G2VPicoLight:
    def __init__(self, ip_address: str = "192.168.1.69", pico_id: str = "00000000c2ca735f"):
        self.ip_address = ip_address
        self.pico_id = pico_id
        self.connection = None
        self._lock = Lock()
        self.channel_list = []

        if G2VPico is None:
            print("❌ AVISO: Librería 'g2vpico' no instalada. (Modo Offline)")
            return

        try:
            self.connection = G2VPico(self.ip_address, self.pico_id)
            # Guardamos la lista de canales disponibles (ej: [1, 2, 3...])
            self.channel_list = self.connection.channel_list 
            print(f"✅ G2V Pico conectada. {self.connection.channel_count} canales detectados.")
        except Exception as e:
            print(f"❌ AVISO: No hay comunicación con G2V Pico en {self.ip_address}. (Modo Offline)")
            self.connection = None

    # ==========================================
    # --- CONTROL BÁSICO ---
    # ==========================================

    def turn_on(self):
        if self.connection:
            with self._lock:
                self.connection.turn_on()
                print("---> [PICO] Lámpara Encendida ☀️")

    def turn_off(self):
        if self.connection:
            with self._lock:
                self.connection.turn_off()
                print("---> [PICO] Lámpara Apagada 🌑")

    def is_fixture_on(self) -> bool:
        """Devuelve True si la lámpara está emitiendo luz actualmente."""
        if self.connection:
            with self._lock:
                return self.connection.is_fixture_on()
        return False

    def clear_all_channels(self):
        if self.connection:
            with self._lock:
                self.connection.clear_channels()
                print("---> [PICO] Todos los canales a 0")

    # ==========================================
    # --- CONTROL Y LECTURA DE CANALES ---
    # ==========================================

    def set_channel(self, channel: int, pwm_value: int):
        if self.connection:
            with self._lock:
                if channel not in self.channel_list:
                    raise ValueError(f"❌ Canal {channel} no existe en este Pico.")
                
                # Obtenemos el límite real de este canal (normalmente 4096)
                limite = self.connection.get_channel_limit(channel)
                if not (0 <= pwm_value <= limite):
                    raise ValueError(f"❌ Valor {pwm_value} fuera de rango (0 - {limite}).")
                
                self.connection.set_channel_value(channel, pwm_value)
                print(f"---> [PICO] Canal {channel} -> {pwm_value}/{limite}")

    def get_channel_value(self, channel: int) -> int:
        """Devuelve la intensidad PWM actual de un canal específico."""
        if self.connection:
            with self._lock:
                return self.connection.get_channel_value(channel)
        return -1

    def get_channel_wavelength_range(self, channel: int) -> list:
        """Devuelve [min_nm, max_nm] para saber qué color emite este canal."""
        if self.connection:
            with self._lock:
                return self.connection.get_channel_wavelength_range(channel)
        return [0.0, 0.0]

    # ==========================================
    # --- CONTROL GLOBAL E INTENSIDAD ---
    # ==========================================

    def set_global_intensity(self, intensity_percent: float):
        if self.connection:
            with self._lock:
                if not (0.0 <= intensity_percent <= 100.0):
                    raise ValueError(f"❌ La intensidad debe estar entre 0.0 y 100.0 (Recibido: {intensity_percent}).")
                self.connection.set_global_intensity(intensity_percent)
                print(f"---> [PICO] Intensidad global al {intensity_percent}%")

    def get_global_intensity(self) -> float:
        """Devuelve el % de intensidad global actual."""
        if self.connection:
            with self._lock:
                return self.connection.get_global_intensity()
        return 0.0

    # ==========================================
    # --- GESTIÓN DE ESPECTROS (JSON / LIST) ---
    # ==========================================

    def get_spectrum(self) -> list:
        """Devuelve una lista de diccionarios con el estado actual de todos los canales."""
        if self.connection:
            with self._lock:
                return self.connection.get_spectrum()
        return []

    def set_spectrum(self, spectrum_data: str):
        """
        Carga un espectro completo.
        Puede recibir un String JSON directo o la RUTA a un archivo .json.
        """
        if self.connection:
            with self._lock:
                datos_a_cargar = spectrum_data
                
                # Si el usuario introduce la ruta a un archivo json, lo leemos
                if spectrum_data.endswith('.json') and os.path.isfile(spectrum_data):
                    try:
                        with open(spectrum_data, 'r') as infile:
                            datos_a_cargar = json.dumps(json.load(infile))
                        print(f"---> [PICO] Cargando espectro desde archivo: {spectrum_data}")
                    except Exception as e:
                        raise ValueError(f"❌ Error al leer el archivo JSON: {e}")

                try:
                    self.connection.set_spectrum(datos_a_cargar)
                    print("---> [PICO] Espectro cargado correctamente.")
                except Exception as e:
                    raise ValueError(f"❌ Error al cargar el espectro: {e}")