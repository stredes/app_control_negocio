# control_negocio/app/utils/exportador.py

import pandas as pd
from pathlib import Path
from datetime import datetime

EXPORT_PATH = Path(__file__).resolve().parent.parent / "exportaciones"
EXPORT_PATH.mkdir(parents=True, exist_ok=True)

class Exportador:
    @staticmethod
    def exportar_excel(nombre_archivo, encabezados, datos):
        try:
            df = pd.DataFrame(datos, columns=encabezados)
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo = EXPORT_PATH / f"{nombre_archivo}_{fecha}.xlsx"
            df.to_excel(archivo, index=False)
            return archivo
        except Exception as e:
            raise Exception(f"No se pudo exportar: {e}")
