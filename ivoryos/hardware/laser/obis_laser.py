import serial
import time
import logging
from threading import Lock

class ObisLaser:
    def __init__(self, port: str = "COM11", timeout: int = 5):
        """
        Controlador para Láser OBIS de Coherent (vía SCPI).
        :param port: Puerto serie (ej. COM11)
        """
        self.port = port
        self.connection = None
        self._lock = Lock()
        
        # Propiedades estáticas cacheadas para no saturar la comunicación
        self._nominal_power = None
        self._max_power = None
        self._min_power = None
        self._wavelength = None

        try:
            # Los equipos SCPI de Coherent usan típicamente 115200 baudios (ajusta si tu manual dice 9600)
            self.connection = serial.Serial(
                port=self.port,
                baudrate=115200, 
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Limpieza del buffer y handshake SCPI (\r\n es obligatorio)
            self.connection.write(b"\r\n")
            time.sleep(0.1)
            self.connection.reset_input_buffer()
            
            # Activar confirmaciones ("handshake = on")
            self._send_command("SYSTem:COMMunicate:HANDshake ON")
            
            # Autodescubrimiento: Le preguntamos al láser quién es
            idn = self._send_command("*IDN?")
            if idn:
                # Cargamos los límites físicos del láser
                self._min_power = float(self._send_command("SOURce:POWer:LIMit:LOW?"))
                self._max_power = float(self._send_command("SOURce:POWer:LIMit:HIGH?"))
                self._wavelength = float(self._send_command("SYSTem:INFormation:WAVelength?"))
                
                print(f"✅ Láser OBIS ({self._wavelength} nm) conectado en {self.port}.")
                print(f"   -> Rango de potencia: {self._min_power} W - {self._max_power} W")
                logging.info(f"LASER OBIS - Conectado. Rango: {self._min_power}-{self._max_power}W")
            else:
                raise serial.SerialException("El Láser no responde al comando de identificación SCPI.")
                
        except Exception as e:
            print(f"❌ AVISO: No hay comunicación con el Láser en {self.port}. (Modo Offline)")
            logging.error(f"LASER OBIS - Error de conexión: {e}")
            self.connection = None


    def _send_command(self, command: str) -> str:
        """Envía comandos SCPI al láser con su terminador obligatorio \\r\\n"""
        if not self.connection: return ""
        with self._lock:
            try:
                cmd = f"{command}\r\n"
                self.connection.write(cmd.encode('ascii'))
                # Los comandos SCPI terminados en '?' esperan respuesta
                if "?" in command:
                    # Leemos hasta el final del terminador \r\n
                    respuesta = self.connection.read_until(b'\r\n').decode('ascii').strip()
                    # Si el handshake "OK" viene pegado, lo limpiamos
                    return respuesta.replace("OK", "").strip() 
                else:
                    # Solo leemos el "OK" de confirmación
                    self.connection.read_until(b'\r\n')
                    return ""
            except Exception as e:
                logging.error(f"Error SCPI en láser: {e}")
                return ""

    # ==========================================
    # --- CONTROL BÁSICO ---
    # ==========================================

    def turn_on(self):
        """Enciende la emisión del láser"""
        if self.connection:
            # Comando SCPI para encender: SOURce:AM:STATe ON
            self._send_command("SOURce:AM:STATe ON")
            print("---> [LÁSER] 🔴 EMISIÓN ENCENDIDA")

    def turn_off(self):
        """Apaga la emisión del láser"""
        if self.connection:
            # Comando SCPI para apagar: SOURce:AM:STATe OFF
            self._send_command("SOURce:AM:STATe OFF")
            print("---> [LÁSER] 🟢 Emisión Apagada")

    def is_emitting(self) -> bool:
        """Devuelve True si el láser está disparando en este momento."""
        resp = self._send_command("SOURce:AM:STATe?")
        # SCPI suele devolver "1" o "ON"
        return "1" in resp or "on" in resp.lower()

    # ==========================================
    # --- CONTROL DE POTENCIA ---
    # ==========================================

    def set_power(self, power_watts: float):
        """
        Ajusta la potencia del láser en Watts (W).
        Valida contra los límites físicos del equipo.
        """
        if self.connection:
            # MURO DE SEGURIDAD FÍSICO
            if self._min_power is not None and self._max_power is not None:
                if power_watts < self._min_power or power_watts > self._max_power:
                    error_msg = f"❌ ERROR: Potencia ({power_watts} W) fuera de los límites del equipo ({self._min_power} W - {self._max_power} W)."
                    print(error_msg)
                    raise ValueError(error_msg) # Lanza Alert en IvoryOS

            # Comando SCPI para fijar nivel de potencia
            self._send_command(f"SOURce:POWer:LEVel:IMMediate:AMPLitude {power_watts}")
            print(f"---> [LÁSER] Potencia ajustada a {power_watts} W")

    def get_actual_power(self) -> float:
        """Lee la potencia real de salida en este momento."""
        resp = self._send_command("SOURce:POWer:LEVel?")
        try:
            return float(resp)
        except:
            return 0.0