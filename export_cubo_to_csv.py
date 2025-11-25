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
# Ejemplo: r"C:\Users\TU_USUARIO\Videos\olap_proyecto"
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

    df = pd.read_sql(query, engine)
    print(f"Filas obtenidas: {len(df)}")

    csv_path = REPO_PATH / CSV_NAME
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"CSV guardado en: {csv_path}")

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

    # Si NO quieres que haga push automático, comenta la siguiente línea:
    # git_commit_and_push(csv_path)

    print("Proceso completado.")
