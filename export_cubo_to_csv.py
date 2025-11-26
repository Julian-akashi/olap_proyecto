import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from datetime import datetime
import subprocess

# ============================
# 1. CONFIGURACIÓN
# ============================

# Datos de conexión a tu MySQL (DW)
DB_USER = "etl_user"
DB_PASSWORD = "TuPasswordFuerte"
DB_HOST = "192.168.0.128"
DB_PORT = 3307
DB_NAME = "db_soporte"

# Ruta LOCAL de tu repo (ajusta esto a tu carpeta real)
REPO_PATH = Path(r"C:\Users\jerry\Videos\olap_proyecto")

# Nombre del CSV dentro del repo (el que usa Streamlit)
CSV_NAME = "vw_cubo_proyectos.csv"

# ============================
# 2. EXPORTAR DESDE MySQL A CSV
# ============================

def exportar_cubo_a_csv():
    print("Conectando a MySQL...")

    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    query = "SELECT * FROM vw_cubo_proyectos"

    df_nuevo = pd.read_sql(query, engine)
    print(f"Filas nuevas obtenidas desde la vista: {len(df_nuevo)}")

    csv_path = REPO_PATH / CSV_NAME

    # Si YA existe un CSV, lo leemos para conservar el historial
    if csv_path.exists():
        print("Leyendo CSV existente para conservar datos anteriores...")
        df_viejo = pd.read_csv(csv_path)

        # Concatenar datos viejos + nuevos
        df_total = pd.concat([df_viejo, df_nuevo], ignore_index=True)

        # Evitar duplicados por idFact si la columna existe
        if "idFact" in df_total.columns:
            df_total = df_total.drop_duplicates(subset=["idFact"], keep="last")
        else:
            # Si no hay idFact, al menos quitamos duplicados exactos
            df_total = df_total.drop_duplicates(keep="last")
    else:
        # Primera vez: solo guardamos lo nuevo
        print("No existía CSV previo, creando uno nuevo...")
        df_total = df_nuevo

    # Guardar todo (viejo + nuevo) en el CSV
    df_total.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"CSV guardado en: {csv_path} (filas totales: {len(df_total)})")

    return csv_path

# ============================
# 3. OPCIONAL: git add / commit / push
# ============================

def git_commit_and_push(csv_path: Path):
    # Mensaje de commit con fecha y hora
    mensaje = f"Auto export cubo OLAP {datetime.now():%Y-%m-%d %H:%M}"

    print("Haciendo git add...")
    subprocess.run(["git", "add", csv_path.name], cwd=REPO_PATH, check=True)

    print("Haciendo git commit...")
    subprocess.run(["git", "commit", "-m", mensaje], cwd=REPO_PATH, check=True)

    print("Haciendo git push...")
    subprocess.run(["git", "push"], cwd=REPO_PATH, check=True)

    print("Cambios enviados a GitHub.")

# ============================
# 4. MAIN
# ============================

if __name__ == "__main__":
    csv_path = exportar_cubo_a_csv()

    # Si NO quieres que haga push automático, deja comentada esta línea
    # git_commit_and_push(csv_path)

    print("Proceso completado.")
