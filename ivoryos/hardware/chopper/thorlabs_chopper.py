import serial
import logging
import threading
import time
import re


def _abrir_puerto_con_timeout(parametros: dict, timeout_s: float = 4.0):
    """
    Intenta abrir un puerto serial en un hilo separado con timeout.
    Evita el cuelgue indefinido que ocurre en Windows cuando un puerto COM
    existe (ej. adaptador USB-Serie) pero no tiene el dispositivo correcto.

    :param parametros: diccionario de kwargs para serial.Serial()
    :param timeout_s: segundos máximos de espera antes de abortar
    :raises TimeoutError: si el puerto no responde en tiempo
    :raises Exception: cualquier otro error de conexión
    """
    resultado = {"conn": None, "error": None}

    def _conectar():
        try:
            resultado["conn"] = serial.Serial(**parametros)
        except Exception as exc:
            resultado["error"] = exc

    hilo = threading.Thread(target=_conectar, daemon=True)
    hilo.start()
    hilo.join(timeout=timeout_s)

    if hilo.is_alive():
        # El hilo sigue bloqueado → el puerto está colgado
        raise TimeoutError(
            f"Timeout ({timeout_s}s) al abrir el puerto. "
            "El puerto existe en Windows pero no responde (dispositivo no conectado)."
        )
    if resultado["error"]:
        raise resultado["error"]
    return resultado["conn"]


class ThorlabsChopper:
    def __init__(self, port: str = "COM6"):
        self.port = port
        self.connection = None
        self._lock = threading.Lock()

        try:
            # Usamos la función con timeout para no quedarnos colgados en Windows
            self.connection = _abrir_puerto_con_timeout({
                "port":     self.port,
                "baudrate": 115200,
                "bytesize": serial.EIGHTBITS,
                "parity":   serial.PARITY_NONE,
                "stopbits": serial.STOPBITS_ONE,
                "timeout":  1.0,
            }, timeout_s=4.0)

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