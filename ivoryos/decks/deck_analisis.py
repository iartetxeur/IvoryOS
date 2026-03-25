import sys
import ivoryos

from ivoryos.hardware.spectrometre.ocean_optics_spectrometer import OceanOpticsSpectrometer

print("🚀 INICIALIZANDO DECK: ANÁLISIS ÓPTICO")

ocean_optics_spectrometer = OceanOpticsSpectrometer()

if __name__ == "__main__":
    try:
        ivoryos.run(__name__, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        # El espectrómetro de Ocean Optics suele cerrarse solo o mediante seabreeze, 
        # pero podemos dejar la estructura por si añades más cosas.
        print("\n[INFO] Apagando Deck de Análisis...")
        sys.exit(0)