import requests
from bs4 import BeautifulSoup
from datetime import datetime

from sgbda.models import actualizaciones

def sync_gdr():
    print("Iniciando sincronización GDR...")

    url = "https://learn.microsoft.com/es-es/troubleshoot/sql/releases/sqlserver-2019/build-versions"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    tables = soup.find_all("table")

    nuevos = 0

    for table in tables:
        rows = table.find_all("tr")

        for row in rows[1:]:
            cols = row.find_all("td")

            if len(cols) < 4:
                continue

            build = cols[0].text.strip()
            kb = cols[1].text.strip()
            descripcion = cols[2].text.strip()
            fecha = cols[3].text.strip()

            # 🔥 FILTRO CLAVE: SOLO GDR
            if "GDR" not in descripcion.upper():
                continue

            # convertir fecha (puede variar formato)
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            except:
                fecha_obj = None

            obj, created = actualizaciones.objects.update_or_create(
                kb=kb,
                defaults={
                    "major_version": "SQL Server",  # puedes mejorar luego
                    "build": build,
                    "descripcion": descripcion,
                    "release_date": fecha_obj,
                    "soportado": True
                }
            )

            if created:
                nuevos += 1

    print(f"Sincronización completada. Nuevos registros: {nuevos}")