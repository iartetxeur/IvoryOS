import serial
import logging
import time
import sys
import threading

try:
    from .channel import Channel
except ImportError:
    pass

# --- Funciones matemáticas (NuMat) ---
def pack_volume2(number: float) -> str:
    """Convierte un número al formato 'mmmmse' (Ej: 1.5 -> '1500+0')."""
    s = f'{abs(number):.3e}'
    return f'{s[0]}{s[2:5]}{s[-3]}{s[-1]}'
    
def pack_discrete2(number: float) -> str:
    """
    Convierte el diámetro (mm) al formato 'Discrete Type 2'.
    Toma un número como 1.14 y lo convierte en '0114' (relleno con ceros a 4 dígitos).
    """
    # Multiplicamos por 100 para quitar decimales (ej: 1.14 -> 114) y formateamos a 4 dígitos
    return f"{int(round(number * 100)):04d}"

class IsmatecPump:
    def __init__(self, port: str = "COM7", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=0.1
            )
            logging.info(f"PUMP Ismatec - Conectada en {port}")
            self.send_command('1~1') # Activar control de canales
            time.sleep(0.1)

        except Exception as e:
            logging.error(f"PUMP Ismatec - Error de conexión: {e}")

    def send_command(self, command: str) -> str:
        if self.connection and self.connection.is_open:
            cmd = command.strip() + "\r"
            self.connection.write(cmd.encode())
            return self.connection.readline().decode().strip()
        return ""

    # --- FUNCIÓN : FLUJO CONTINUO ---
    def start_pumping(self, channel_index: int = 1, flow_rate_ml_min: float = 1.0, direction: str = "CW"):
        if self.connection:
            try:
                self.send_command(f"{channel_index}xf1") # Forzar unidad a FlowRate
                self.send_command(f"{channel_index}M")
                dir_cmd = "J" if direction == "CW" else "K"
                self.send_command(f"{channel_index}{dir_cmd}")
                
                self.send_command(f"{channel_index}f{pack_volume2(flow_rate_ml_min)}")
                self.send_command(f"{channel_index}H")
            except Exception as e:
                logging.error(f"Error: {e}")

    def set_tubing_diameter(self, channel_index: int = 1, tubing_diam_mm: float = 1.14):
        """
        Configura el diámetro interno del tubo para un canal específico.
        """
        if self.connection:
            try:
                # El comando es + (plus) seguido del valor empaquetado
                packed_diam = pack_discrete2(tubing_diam_mm)
                self.send_command(f"{channel_index}+{packed_diam}")
                
                logging.info(f"Canal {channel_index}: Diámetro configurado a {tubing_diam_mm} mm")
                print(f"---> [CONFIG] Canal {channel_index} | Tubo: {tubing_diam_mm} mm (Cód: {packed_diam})")
            except Exception as e:
                logging.error(f"Error al configurar diámetro: {e}")

    # --- FUNCIÓN : DOSIFICAR VOLUMEN CON BARRA DE PROGRESO ---
    def dispense_volume(self, channel_index: int = 1, volume_ml: float = 1.0, flow_rate_ml_min: float = 1.0, direction: str = "CW"):
        """Dosifica una cantidad exacta y muestra una barra de progreso."""
        if self.connection:
            try:
                # 1. Forzar que la velocidad se entienda como mL/min (Comando xf1)
                self.send_command(f"{channel_index}xf1")
                
                # 2. Poner en Modo "Volumen a Caudal" ('O')
                self.send_command(f"{channel_index}O")
                
                # 3. Dirección
                dir_cmd = "J" if direction == "CW" else "K"
                self.send_command(f"{channel_index}{dir_cmd}")
                
                # 4. Enviar Caudal y Volumen correctos
                self.send_command(f"{channel_index}f{pack_volume2(flow_rate_ml_min)}")
                self.send_command(f"{channel_index}v{pack_volume2(volume_ml)}")
                
                # 5. Arrancar la bomba
                self.send_command(f"{channel_index}H")
                
                # --- CÁLCULO DE TIEMPO Y BARRA DE PROGRESO ---
                tiempo_segundos = (volume_ml / flow_rate_ml_min) * 60
                print(f"\n---> [DOSIFICANDO] {volume_ml} mL a {flow_rate_ml_min} mL/min.")
                print(f"---> [TIEMPO ESTIMADO] {tiempo_segundos:.1f} segundos.")
                
                # Lanzamos la barra de progreso en segundo plano para no bloquear IvoryOS
                threading.Thread(
                    target=self._barra_fija_progreso, 
                    args=(tiempo_segundos, volume_ml), 
                    daemon=True
                ).start()
                
            except Exception as e:
                logging.error(f"Error al dispensar volumen: {e}")

    def _barra_fija_progreso(self, duracion_total: float, vol_objetivo: float):
        """Dibuja una barra de 40 caracteres que se rellena visualmente."""
        ancho_barra = 40
        inicio = time.time()
        
        print(f"\n[INFO] Dosificando {vol_objetivo} mL. Por favor, espere...")
        
        while True:
            transcurrido = time.time() - inicio
            porcentaje = min(transcurrido / duracion_total, 1.0)
            
            # Calculamos cuántos bloques llenar y cuántos espacios dejar
            lleno = int(ancho_barra * porcentaje)
            vacio = ancho_barra - lleno
            
           
            barra = "█" * lleno + "-" * vacio
            sys.stdout.write(f"\rEstado: [{barra}] {int(porcentaje * 100)}% ({transcurrido:.1f}s / {duracion_total:.1f}s)")
            sys.stdout.flush()
            
            if porcentaje >= 1.0:
                print(f"\n[OK] Dispensación de {vol_objetivo} mL completada con éxito.\n")
                break
            
            time.sleep(0.1) # Actualización fluida cada 100ms

    # --- FUNCIÓN DE CALIBRACIÓN ---
    def set_calibration_value(self, channel_index: int = 1, measured_volume_ml: float = 1.0):
        """
        Envía a la bomba el volumen real medido para calibrar el canal.
        El usuario debe haber dispensado un volumen teórico y pesado el resultado.
        """
        if self.connection:
            try:
                # El comando para enviar el valor real de calibración es '#' o '+' según modo
                # Usamos el formato de volumen empaquetado para el valor medido
                packed_val = pack_volume2(measured_volume_ml)
                self.send_command(f"{channel_index}#{packed_val}")
                
                print(f"---> [CALIBRACIÓN] Canal {channel_index} ajustado a {measured_volume_ml} mL.")
                logging.info(f"Calibración completada en canal {channel_index}")
            except Exception as e:
                logging.error(f"Error en calibración: {e}")

    # --- FUNCIÓN : PARAR ---
    def stop_pumping(self, channel_index: int = 1):
        if self.connection:
            self.send_command(f"{channel_index}I")
            print(f"---> [PARADA FORZADA] Canal {channel_index}")