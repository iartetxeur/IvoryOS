import logging
import time
from ismatec import RegloICC as Ismatec

class IsmatecPump:
    def __init__(self, port: str = "COM7"):
        """
        Inicializa la conexión con la bomba Ismatec.
        :param port: Puerto COM donde está conectada la bomba.
        """
        self.pump = None
        try:
            # Inicializamos tu clase original
            self.pump = Ismatec(port=port)
            logging.info(f"PUMP - Ismatec conectada con éxito en {port}")
        except Exception as e:
            logging.error(f"PUMP - No se pudo conectar a la bomba en {port}: {e}")

    def start_pumping(self, channel_index: int = 1, flow_rate: float = 1.0, direction: str = "CW"):
        """
        Activa un canal de la bomba.
        :param channel_index: Índice del canal (1-4).
        :param flow_rate: Velocidad de flujo.
        :param direction: 'CW' para horario, 'CCW' para antihorario.
        """
        if self.pump:
            try:
                channel = self.pump.channels[channel_index - 1]
                channel.set_flow_rate(flow_rate)
                channel.set_direction(direction)
                channel.start()
                logging.info(f"Canal {channel_index} iniciado a {flow_rate} ml/min")
            except Exception as e:
                logging.error(f"Error al iniciar bombeo: {e}")

    def stop_pumping(self, channel_index: int = 1):
        """Detiene un canal específico."""
        if self.pump:
            try:
                self.pump.channels[channel_index - 1].stop()
                logging.info(f"Canal {channel_index} detenido.")
            except Exception as e:
                logging.error(f"Error al detener bomba: {e}")

    def stop_all(self):
        """Detiene todos los canales de seguridad."""
        if self.pump:
            for i in range(len(self.pump.channels)):
                self.stop_pumping(i + 1)

    def close_connection(self):
        """Cierra el puerto serie."""
        if self.pump:
            self.stop_all()
            self.pump.close()
            logging.info("Conexión con Ismatec cerrada.")