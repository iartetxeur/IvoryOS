"""
IkaStirrerWithLogging - IKA RCT 5 con registro automatico de temperatura
=========================================================================
Extiende IkaStirrer anadiendo registro continuo de temperatura en segundo
plano. El registro empieza automaticamente al encender la calefaccion o
el motor, y guarda el CSV + grafica PNG al apagar ambos.

Los archivos se guardan en: IvoryOS/reports/
"""

import time
import threading
import logging
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from ivoryos.hardware.stirrer.ika_stirrer import IkaStirrer

_REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


class IkaStirrerWithLogging(IkaStirrer):
    """
    IKA RCT 5 con registro automatico de temperatura.
    El log arranca solo al encender calefaccion o motor,
    y se guarda automaticamente al apagarlos.
    """

    def __init__(self, port: str = "COM5", interval_seconds: int = 30):
        """
        :param port: Puerto COM del IKA.
        :param interval_seconds: Segundos entre lecturas de temperatura.
        """
        super().__init__(port=port)
        self._interval = interval_seconds
        self._log_data = []
        self._running = False
        self._thread = None
        self._heating_on = False
        self._stirring_on = False
        self._experiment_name = ""
        self._csv_path = None
        self._plot_path = None
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # --- CALEFACCION (con log automatico) ---
    # ==========================================

    def start_heating(self):
        """Enciende la calefaccion e inicia el registro de temperatura."""
        super().start_heating()
        self._heating_on = True
        self._start_logging_if_needed()

    def stop_heating(self):
        """Apaga la calefaccion. Si el motor tambien esta parado, guarda el informe."""
        super().stop_heating()
        self._heating_on = False
        self._stop_logging_if_done()

    # ==========================================
    # --- AGITACION (con log automatico) ---
    # ==========================================

    def start_stirring(self):
        """Inicia el motor e inicia el registro de temperatura."""
        super().start_stirring()
        self._stirring_on = True
        self._start_logging_if_needed()

    def stop_stirring(self):
        """Para el motor. Si la calefaccion tambien esta apagada, guarda el informe."""
        super().stop_stirring()
        self._stirring_on = False
        self._stop_logging_if_done()

    # ==========================================
    # --- LOGICA INTERNA ---
    # ==========================================

    def _start_logging_if_needed(self):
        if self._running:
            return
        self._log_data = []
        self._experiment_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._csv_path  = _REPORTS_DIR / f"temperatura__{self._experiment_name}.csv"
        self._plot_path = _REPORTS_DIR / f"temperatura__{self._experiment_name}.png"
        self._running = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        print(f"[LOG] Registro de temperatura iniciado: {self._experiment_name}")

    def _stop_logging_if_done(self):
        if self._heating_on or self._stirring_on:
            return  # Todavia hay algo encendido, seguir registrando
        if not self._running:
            return

        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        if not self._log_data:
            print("[LOG] No se registraron datos.")
            return

        df = pd.DataFrame(self._log_data)
        df.to_csv(self._csv_path, index=False)
        self._generate_plot(df)
        print(f"[LOG] Informe guardado:")
        print(f"      CSV:     {self._csv_path}")
        print(f"      Grafica: {self._plot_path}")

    def _record_loop(self):
        while self._running:
            try:
                probe_temp    = self.get_external_temp()
                hotplate_temp = self.get_hotplate_temp()
                self._log_data.append({
                    "Timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Sonda (C)":  probe_temp,
                    "Placa (C)":  hotplate_temp,
                })
                if len(self._log_data) % 10 == 0:
                    pd.DataFrame(self._log_data).to_csv(self._csv_path, index=False)
            except Exception as e:
                logging.error(f"[TemperatureLogger] Error en lectura: {e}")

            for _ in range(self._interval):
                if not self._running:
                    break
                time.sleep(1)

    # ==========================================
    # --- GENERACION DE GRAFICA ---
    # ==========================================

    def _generate_plot(self, df: pd.DataFrame):
        df["Datetime"] = pd.to_datetime(df["Timestamp"])

        fig, ax1 = plt.subplots(figsize=(14, 6))

        ax1.set_xlabel("Tiempo")
        ax1.set_ylabel("Temperatura Sonda (C)", color="tab:blue")
        line1, = ax1.plot(df["Datetime"], df["Sonda (C)"],
                          color="tab:blue", linestyle="-", linewidth=2, label="Sonda (externa)")
        ax1.tick_params(axis="y", labelcolor="tab:blue")

        ax2 = ax1.twinx()
        ax2.set_ylabel("Temperatura Placa (C)", color="tab:red")
        line2, = ax2.plot(df["Datetime"], df["Placa (C)"],
                          color="tab:red", linestyle="--", linewidth=2, label="Placa (interna)")
        ax2.tick_params(axis="y", labelcolor="tab:red")

        ymin = min(df["Sonda (C)"].min(), df["Placa (C)"].min()) - 5
        ymax = max(df["Sonda (C)"].max(), df["Placa (C)"].max()) + 5
        ax1.set_ylim(ymin, ymax)
        ax2.set_ylim(ymin, ymax)

        ax1.legend(handles=[line1, line2], loc="upper left", fontsize=9)
        plt.title(f"Registro de Temperatura — {self._experiment_name}", fontsize=13)
        plt.xticks(rotation=40, ha="right")
        plt.tight_layout()
        plt.savefig(self._plot_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
