import serial
import logging
import threading
import time
import sys
import re

class IkaStirrer:
    def __init__(self, port: str = "COM5"):
        # 1. Definir la variable ANTES de que nada pueda fallar
        self.port = port 
        self.connection = None
        self._lock = threading.Lock()

        try:
            # 2. Configuración que acabamos de verificar (8N1)
            self.connection = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=1.0
            )
            
            # Limpiar rastro de intentos fallidos
            self.connection.reset_input_buffer()
            
            # 3. Verificación con el comando que SI ha funcionado
            self.connection.write(b"IN_NAME\r\n")
            time.sleep(0.5) 
            respuesta = self.connection.read_all().decode('ascii', errors='ignore').strip()
            
            # CAMBIO CRITICO: Aceptamos "RCT" o "IKA" o cualquier respuesta no vacía
            if "RCT" in respuesta or "IKA" in respuesta or len(respuesta) > 0:
                print(f"✅ Placa IKA detectada ({respuesta}) en {self.port}")
            else:
                raise serial.SerialException("La placa no respondió correctamente al nombre.")
                
        except Exception as e:
            print(f"❌ AVISO: No hay comunicación con la Placa IKA en {self.port}. (Modo Offline)")
            self.connection = None

    def send_command(self, command: str) -> str:
        """Envía el comando con el terminador estándar de IKA (Carriage Return + Line Feed)."""
        if self.connection and self.connection.is_open:
            with self._lock:
                # IKA exige que cada comando termine en \r\n y codificado en ASCII
                cmd = command.strip() + "\r\n"
                self.connection.write(cmd.encode('ascii'))
                time.sleep(0.05) # Pequeña pausa de seguridad para que el microprocesador de IKA lo lea
                return self.connection.readline().decode('ascii').strip()
        return ""

    def _extract_number(self, response: str) -> float:
        """Usa Expresiones Regulares (Regex) para extraer el número exacto de la respuesta de IKA."""
        if not response: return -999.0
        # Esta "trampa matemática" busca números, decimales y notación científica, ignorando el texto
        matches = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", response)
        if matches:
            return float(matches[0])
        return -999.0

    # ==========================================
    # --- CONTROL Y LECTURA DE AGITACIÓN (Motor) ---
    # ==========================================
    
    def set_rpm(self, target_rpm: int = 500):
        """Ajusta la velocidad de agitación. El comando NAMUR es 'OUT_SP_4'."""
        self.send_command(f"OUT_SP_4 {target_rpm}")
        print(f"---> [AGITADOR] Velocidad configurada a {target_rpm} RPM")

    def start_stirring(self):
        """Inicia el giro del imán del motor."""
        self.send_command("START_4")
        print("---> [AGITADOR] Motor encendido")

    def stop_stirring(self):
        """Detiene la rotación del imán."""
        self.send_command("STOP_4")
        print("---> [AGITADOR] Motor detenido")

    def get_stirring_speed(self) -> float:
        """
        Lee a cuántas revoluciones por minuto (RPM) está girando el motor en este instante.
        El comando NAMUR es 'IN_PV_4'.
        Sirve para comprobar que el imán no se ha 'desacoplado' o saltado si el líquido es muy viscoso.
        """
        respuesta = self.send_command("IN_PV_4")
        return self._extract_number(respuesta)

    # ==========================================
    # --- CONTROL Y LECTURA DE TEMPERATURA (Placa) ---
    # ==========================================
    
    def set_temperature(self, temp_celsius: float = 25.0):
        """Ajusta la temperatura objetivo de la placa. El comando NAMUR es 'OUT_SP_1'."""
        self.send_command(f"OUT_SP_1 {temp_celsius}")
        print(f"---> [CALEFACCIÓN] Temperatura objetivo configurada a {temp_celsius} °C")

    def start_heating(self):
        """Enciende la resistencia de calentamiento de la placa."""
        self.send_command("START_1")
        print("---> [CALEFACCIÓN] Encendida")

    def stop_heating(self):
        """Apaga la resistencia térmica."""
        self.send_command("STOP_1")
        print("---> [CALEFACCIÓN] Apagada")

    def get_hotplate_temp(self) -> float:
        """
        Pregunta a la placa cuál es la temperatura de la superficie metálica (el sensor interno).
        El comando NAMUR es 'IN_PV_2'.
        Fundamental por seguridad para evitar sobrecalentamientos de la máquina.
        """
        respuesta = self.send_command("IN_PV_2")
        return self._extract_number(respuesta)

    def get_external_temp(self) -> float:
        """
        Lee la temperatura que mide el termopar externo (la sonda PT1000 que metes en el líquido).
        El comando NAMUR es 'IN_PV_1'.
        Esta es la función principal para saber la temperatura real del medio de reacción.
        """
        respuesta = self.send_command("IN_PV_1")
        return self._extract_number(respuesta)

    def get_temperature(self, sensor: str = "probe") -> float:
        """
        Función unificada para leer la temperatura actual de la placa IKA.
        - 'probe': Usa la sonda externa (IN_PV_1).
        - 'hotplate': Usa el sensor de la placa base (IN_PV_2).
        """
        if sensor == "probe":
            return self.get_external_temp()
        else:
            return self.get_hotplate_temp()

    def wait_for_temperature(self, target_temp: float, tolerance: float = 2.0, sensor: str = "probe"):
        """
        Pausa el experimento de IvoryOS hasta que se alcance la temperatura objetivo.
        La 'tolerancia' permite aceptar un rango válido (ej: objetivo 120 ± 2 °C).
        Es vital para esperar antes de inyectar los precursores de las nanopartículas.
        """
        print(f"\n[INFO] Esperando alcanzar {target_temp} °C (Tolerancia: ±{tolerance} °C) usando sensor '{sensor}'...")
        
        while True:
            current_temp = self.get_temperature(sensor)
            
            # Imprimir en consola actualizándose (con \r para no llenar la pantalla de texto)
            sys.stdout.write(f"\r---> Temperatura actual: {current_temp} °C / Objetivo: {target_temp} °C")
            sys.stdout.flush()
            
            # Comprobar si hemos llegado (usando el valor absoluto de la diferencia)
            if current_temp != -999.0 and abs(current_temp - target_temp) <= tolerance:
                print(f"\n[OK] Temperatura de {current_temp} °C alcanzada. ¡Continuando experimento!")
                break
                
            # Esperar 2 segundos para no saturar el cable USB
            time.sleep(2.0)

    def wait_for_stirring(self, target_rpm: int, tolerance: int = 10):
        """
        Pausa el experimento en IvoryOS hasta que el motor alcance las RPM deseadas.
        - target_rpm: La velocidad que quieres alcanzar.
        - tolerance: El margen de error aceptado (ej: ±10 RPM).
        """
        print(f"\n[INFO] Esperando a alcanzar {target_rpm} RPM (Tolerancia: ±{tolerance} RPM)...")
        
        while True:
            # Usamos la función que lee la velocidad REAL del motor (IN_PV_4)
            current_rpm = self.get_stirring_speed()
            
            sys.stdout.write(f"\r---> Velocidad actual: {current_rpm} RPM / Objetivo: {target_rpm} RPM")
            sys.stdout.flush()
            
            # Comprobamos si la velocidad actual está dentro del rango
            if current_rpm != -999.0 and abs(current_rpm - target_rpm) <= tolerance:
                print(f"\n[OK] Velocidad de {current_rpm} RPM alcanzada. ¡Continuando!")
                break
            
            time.sleep(1.0)