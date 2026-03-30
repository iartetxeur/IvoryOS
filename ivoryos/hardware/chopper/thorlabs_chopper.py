import serial
import logging
import threading
import time
import re

class ThorlabsChopper:
    def __init__(self, port: str = "COM6"):
        self.port = port
        self.connection = None
        self._lock = threading.Lock()

        try:
            # Los parámetros exactos de comunicación extraídos del archivo original
            self.connection = serial.Serial(
                port=self.port,
                baudrate=115200,                # Velocidad requerida por Thorlabs
                bytesize=serial.EIGHTBITS,      # 8 bits de datos
                parity=serial.PARITY_NONE,      # Sin paridad
                stopbits=serial.STOPBITS_ONE,   # 1 bit de parada
                timeout=1.0
            )
            
            # Limpiar el buffer mandando un 'Carriage Return' inicial
            self.connection.write(b"\r")
            time.sleep(0.1)
            self.connection.reset_input_buffer()
            
            # Verificación de estado pidiendo la frecuencia interna
            self.connection.write(b"freq?\r")
            time.sleep(0.1)
            respuesta = self.connection.read_all().decode('ascii', errors='ignore')
            
            if "freq=" in respuesta.lower() or len(respuesta) > 2:
                print(f"✅ Chopper Thorlabs conectado correctamente en {port}")
                logging.info(f"CHOPPER - Conectado en {port}")
            else:
                raise serial.SerialException("El chopper no responde al handshake.")

        except Exception as e:
            print(f"❌ AVISO: No hay comunicación con el Chopper en {self.port}. (Modo Offline)")
            logging.error(f"CHOPPER - Error de conexión: {e}")
            self.connection = None

    def send_command(self, command: str) -> str:
        """Envía comandos al chopper. Thorlabs exige terminación '\\r'."""
        if self.connection and self.connection.is_open:
            with self._lock:
                # El comando DEBE terminar en retorno de carro (\r)
                cmd = f"{command.strip()}\r"
                self.connection.write(cmd.encode('ascii'))
                time.sleep(0.05) # Pequeño retardo de seguridad
                return self.connection.read_all().decode('ascii', errors='ignore').strip()
        return ""

    def start(self):
        """Inicia la rotación del disco."""
        # El comando original documentado es enable=1
        self.send_command("enable=1")
        print("---> [CHOPPER] Motor encendido")

    def stop(self):
        """Detiene la rotación del disco."""
        # El comando original documentado es enable=0
        self.send_command("enable=0")
        print("---> [CHOPPER] Motor detenido")

    def set_frequency(self, freq_hz: int = 100):
        """
        Ajusta la frecuencia de corte (Hz). 
        El rango permitido depende del disco (blade) físico que tengas puesto.
        """
        self.send_command(f"freq={freq_hz}")
        print(f"---> [CHOPPER] Frecuencia objetivo: {freq_hz} Hz")

    def get_frequency(self) -> float:
        """Consulta la frecuencia real a la que está girando el motor en este instante."""
        respuesta = self.send_command("freq?")
        
        # Usamos RegEx para sacar los números de una respuesta tipo "freq=100.0\r"
        matches = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", respuesta)
        if matches:
            return float(matches[0])
        return -999.0

    def get_status(self) -> bool:
        """Verifica si el motor está girando (True) o parado (False)."""
        respuesta = self.send_command("enable?")
        return "1" in respuesta