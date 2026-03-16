import serial
import logging
from .channel import Channel
import os

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
            logging.info(f"PUMP - Conectada vía Serie en {port}")
        except Exception as e:
            logging.error(f"PUMP - Error de conexión: {e}")

    def send_command(self, command: str) -> str:
        if self.connection and self.connection.is_open:
            self.connection.write(command.encode())
            return self.connection.readline().decode()
        return ""

    def start_pumping(self, channel_index: int = 1, flow_rate: float = 1.0, direction: str = "CW"):
        """Orden directa a la bomba"""
        if self.connection:
            # Comandos directos según el protocolo de tu compañero
            dir_cmd = "J" if direction == "CW" else "K"
            self.send_command(f"{channel_index}{dir_cmd}\r\n") # Dirección
            self.send_command(f"{channel_index}H\r\n")         # Arrancar
            logging.info(f"Canal {channel_index} en marcha.")

    def stop_pumping(self, channel_index: int = 1):
        """Parada directa"""
        if self.connection:
            self.send_command(f"{channel_index}I\r\n")
            logging.info(f"Canal {channel_index} detenido.")