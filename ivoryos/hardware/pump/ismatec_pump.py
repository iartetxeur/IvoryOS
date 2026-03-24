import serial
import logging
import time
import sys
import threading

try:
    from .channel import Channel
except ImportError:
    pass

# --- Funciones matemáticas (Extraídas del protocolo NuMat) ---

def pack_volume2(number: float) -> str:
    """
    Convierte un número decimal normal al formato 'mmmmse' que exige la Reglo ICC.
    Ejemplo: 1.5 -> '1.500e+00' -> '1500+0'
    Esto se usa para enviar Caudales y Volúmenes.
    """
    s = f'{abs(number):.3e}'
    return f'{s[0]}{s[2:5]}{s[-3]}{s[-1]}'
    
def pack_discrete2(number: float) -> str:
    """
    Convierte el diámetro del tubo (mm) al formato 'Discrete Type 2'.
    Toma un número como 1.14, lo multiplica por 100 para quitar decimales (114) 
    y lo rellena con ceros a 4 dígitos: '0114'.
    """
    return f"{int(round(number * 100)):04d}"

class IsmatecPump:
    def __init__(self, port: str = "COM8", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self._lock = threading.Lock() 
        self._stop_events = {} 

        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=0.1
            )
            # Imprimimos el éxito en consola para que lo veas claro
            print(f"✅ Bomba Ismatec conectada correctamente en {port}")
            logging.info(f"PUMP Ismatec - Conectada en {port}")
            
            # COMANDO CORRECTO PARA DESPERTARLA: 1~1 (Bomba 1, Activa canales)
            self.send_command('1~1') 
            time.sleep(0.1)

        except Exception as e:
            logging.error(f"PUMP Ismatec - Error de conexión: {e}")

    def send_command(self, command: str) -> str:
        """Envía el comando limpio. La variable 'command' ya incluye el número de canal."""
        if self.connection and self.connection.is_open:
            with self._lock:
                # Quitamos el self.address. Ahora si envías "1H", viajará exactamente "1H\r"
                clean_cmd = command.strip()
                full_payload = f"{clean_cmd}\r" 
                
                self.connection.write(full_payload.encode('ascii'))
                time.sleep(0.05) 
                return self.connection.readline().decode('ascii').strip()
        return ""
    # --- FUNCIÓN 1: FLUJO CONTINUO ---
    def start_pumping(self, channel_index: int = 1, flow_rate_ml_min: float = 1.0, direction: str = "CW"):
        """Inicia el bombeo infinito. El usuario o el código debe enviar 'stop_pumping' para detenerlo."""
        
        # Si arrancamos en continuo, cancelamos cualquier barra de progreso (dosificación) que estuviera corriendo
        if channel_index in self._stop_events:
            self._stop_events[channel_index].set()

        if self.connection:
            try:
                # 1. Comando 'xf1': Forzar unidad a FlowRate (mL/min) en lugar de RPM
                self.send_command(f"{channel_index}xf1") 
                # 2. Comando 'M': Poner en Modo Flujo Continuo
                self.send_command(f"{channel_index}M")
                # 3. Dirección: 'J' para ClockWise (CW), 'K' para CounterClockWise (CCW)
                dir_cmd = "J" if direction == "CW" else "K"
                self.send_command(f"{channel_index}{dir_cmd}")
                
                # 4. Comando 'f': Enviar el caudal empaquetado matemáticamente
                self.send_command(f"{channel_index}f{pack_volume2(flow_rate_ml_min)}")
                # 5. Comando 'H': Arrancar la bomba (Start)
                self.send_command(f"{channel_index}H")
            except Exception as e:
                logging.error(f"Error al iniciar bombeo continuo: {e}")

    # --- FUNCIÓN 2: CONFIGURACIÓN DE TUBO ---
    def set_tubing_diameter(self, channel_index: int = 1, tubing_diam_mm: float = 1.14):
        """
        Configura el diámetro interno del tubo. 
        CRÍTICO para que los cálculos internos de mL/min y volúmenes de la bomba sean exactos.
        """
        if self.connection:
            try:
                # El comando es '+' (plus) seguido del diámetro empaquetado a 4 dígitos
                packed_diam = pack_discrete2(tubing_diam_mm)
                self.send_command(f"{channel_index}+{packed_diam}")
                
                logging.info(f"Canal {channel_index}: Diámetro configurado a {tubing_diam_mm} mm")
                print(f"---> [CONFIG] Canal {channel_index} | Tubo: {tubing_diam_mm} mm")
            except Exception as e:
                logging.error(f"Error al configurar diámetro: {e}")

    # --- FUNCIÓN 3: DOSIFICAR VOLUMEN CON BARRA DE PROGRESO ---
    def dispense_volume(self, channel_index: int = 1, volume_ml: float = 1.0, flow_rate_ml_min: float = 1.0, direction: str = "CW"):
        """La bomba dosifica una cantidad exacta y su propio cerebro la detiene al llegar al objetivo."""
        
        # 1. Si el usuario hace doble clic o lanza varias seguidas, cancelamos la barra anterior
        if channel_index in self._stop_events:
            self._stop_events[channel_index].set()
            time.sleep(0.2) # Damos tiempo al hilo anterior a cerrarse
            
        # 2. Creamos un nuevo "interruptor" para la nueva barra de este canal específico
        stop_event = threading.Event()
        self._stop_events[channel_index] = stop_event

        if self.connection:
            try:
                # Forzar mL/min
                self.send_command(f"{channel_index}xf1")
                # Comando 'O': Poner la bomba en Modo "Volumen a Caudal" (Se parará sola)
                self.send_command(f"{channel_index}O")
                
                # Dirección
                dir_cmd = "J" if direction == "CW" else "K"
                self.send_command(f"{channel_index}{dir_cmd}")
                
                # Enviar Caudal ('f') y Volumen ('v') empaquetados
                self.send_command(f"{channel_index}f{pack_volume2(flow_rate_ml_min)}")
                self.send_command(f"{channel_index}v{pack_volume2(volume_ml)}")
                
                # Arrancar la bomba ('H')
                self.send_command(f"{channel_index}H")
                
                # Calcular el tiempo teórico para poder dibujar la barra visual
                tiempo_segundos = (volume_ml / flow_rate_ml_min) * 60
                
                # Lanzamos la barra de progreso en un hilo en segundo plano (daemon=True)
                threading.Thread(
                    target=self._barra_fija_progreso, 
                    args=(tiempo_segundos, volume_ml, stop_event, channel_index), 
                    daemon=True
                ).start()
                
            except Exception as e:
                logging.error(f"Error al dispensar volumen: {e}")

    def _barra_fija_progreso(self, duracion_total: float, vol_objetivo: float, stop_event: threading.Event, ch: int):
        """
        Dibuja una barra de 40 caracteres en consola.
        Se cancelará inmediatamente si el stop_event se pone en rojo (ej: el usuario paró la bomba).
        """
        ancho_barra = 40
        inicio = time.time()
        
        print(f"\n[INFO] Dosificando {vol_objetivo} mL en Canal {ch}. Por favor, espere...")
        
        # Bucle principal: se repite mientras nadie toque el "interruptor"
        while not stop_event.is_set():
            transcurrido = time.time() - inicio
            porcentaje = min(transcurrido / duracion_total, 1.0)
            
            # Calcular bloques pintados (█) y vacíos (-)
            lleno = int(ancho_barra * porcentaje)
            vacio = ancho_barra - lleno
            barra = "█" * lleno + "-" * vacio
            
            # \r hace que el texto se sobreescriba en la misma línea. Mostramos el canal [C{ch}] para distinguirlos.
            sys.stdout.write(f"\r[C{ch}] Estado: [{barra}] {int(porcentaje * 100)}% ({transcurrido:.1f}s / {duracion_total:.1f}s)")
            sys.stdout.flush()
            
            if porcentaje >= 1.0:
                print(f"\n[OK] Dispensación de {vol_objetivo} mL en Canal {ch} completada.\n")
                break
            
            time.sleep(0.1) # Refresco visual fluido a 10 fps
            
        # Si el bucle se rompió porque alguien tocó el interruptor (stop manual) antes de llegar al 100%
        if stop_event.is_set() and porcentaje < 1.0:
            print(f"\n[!] Dispensación cancelada en Canal {ch}.")

    # --- FUNCIÓN 4: CALIBRACIÓN DE PRECISIÓN ---
    def set_calibration_value(self, channel_index: int = 1, measured_volume_ml: float = 1.0):
        """
        Envía a la bomba el volumen real medido con balanza para calibrar el canal.
        El usuario debe haber dispensado un volumen teórico previamente.
        """
        if self.connection:
            try:
                # El comando para enviar el valor real medido y calibrar es '#'
                packed_val = pack_volume2(measured_volume_ml)
                self.send_command(f"{channel_index}#{packed_val}")
                
                print(f"---> [CALIBRACIÓN] Canal {channel_index} ajustado a {measured_volume_ml} mL.")
                logging.info(f"Calibración completada en canal {channel_index}")
            except Exception as e:
                logging.error(f"Error en calibración: {e}")

    # --- FUNCIÓN 5: PARAR ---
    def stop_pumping(self, channel_index: int = 1):
        """Comando de parada forzada. Actúa también como 'Emergency Stop' para la barra visual."""
        if self.connection:
            # Comando 'I': Halt / Stop
            self.send_command(f"{channel_index}I")
            print(f"\n---> [PARADA FORZADA] Comando STOP enviado al Canal {channel_index}")
            
            # Al darle a parar, "apagamos" el interruptor de la barra de progreso de este canal para que se borre de pantalla
            if channel_index in self._stop_events:
                self._stop_events[channel_index].set()