import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sgbda.models import actualizaciones
import re

import requests
import re
from datetime import datetime


import requests
import re
from datetime import datetime

def sync_gdr():
    print("Iniciando sincronización GDR...")

    URLS_SQL = {
        "2016": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2016/build-versions.md",
        "2017": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2017/build-versions.md",
        "2019": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2019/build-versions.md",
        "2022": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2022/build-versions.md",
    }

    FORMATOS_FECHA = ["%B %d, %Y", "%Y-%m-%d", "%d/%m/%Y"]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    nuevos = 0

    def es_gdr(descripcion):

        desc = descripcion.upper().strip()

        return bool(
            re.match(r'^(SP\d+\s*\+\s*GDR|CU\d+\s*\+\s*GDR)$', desc)
        )

    def parsear_fila(cols, version):
        """
        Extrae (descripcion, build, kb, fecha_raw) según la estructura real por versión.

        2016 → 4 cols: [descripcion | build | KB | fecha]
        2017/2019/2022 → 7 cols: [descripcion | build | sqlservr | AS build | AS file | KB | fecha]
        """
        if version == "2016":
            if len(cols) < 4:
                return None
            return cols[0], cols[1], cols[2], cols[3]
        else:
            if len(cols) < 7:
                return None
            return cols[0], cols[1], cols[5], cols[6]

    for version, url in URLS_SQL.items():
        print(f"\nProcesando SQL Server {version}...")

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  ⚠️  Error de red: {e}")
            continue

        for linea in response.text.splitlines():
            # Solo filas de tabla, descartar separadores
            if not linea.startswith("|"):
                continue
            if re.match(r'^\s*\|[\s\-:]+\|', linea):
                continue

            cols = [c.strip() for c in linea.strip("|").split("|")]
            # Limpiar markdown links: [texto](url) → texto
            cols = [re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', c) for c in cols]
            # Limpiar bold: **texto** → texto
            cols = [re.sub(r'\*\*([^*]+)\*\*', r'\1', c) for c in cols]

            resultado = parsear_fila(cols, version)
            if not resultado:
                continue

            descripcion, build, kb_raw, fecha_raw = resultado

            # Saltar encabezados de tabla
            if re.search(r'(?i)cumulative update name|gdr name|sp name|build version|product version|knowledge base|release date', descripcion):
                continue

            # Filtro: solo GDR y sus variantes
            if not es_gdr(descripcion):
                continue

            # Limpiar KB → solo número
            kb = re.sub(r'(?i)^kb', '', kb_raw).strip()

            # Parsear fecha
            fecha_obj = None
            for fmt in FORMATOS_FECHA:
                try:
                    fecha_obj = datetime.strptime(fecha_raw.strip(), fmt).date()
                    break
                except ValueError:
                    continue

            if not kb or not build:
                continue

            print(f"  ✅ [{version}] {descripcion} | Build: {build} | KB: {kb} | Fecha: {fecha_obj}")

            try:
                obj, created = actualizaciones.objects.update_or_create(
                    kb=kb,
                    defaults={
                        "major_version": version,
                        "build":         build,
                        "descripcion":   descripcion,
                        "release_date":  fecha_obj,
                        "soportado":     True,
                    }
                )
                if created:
                    nuevos += 1
            except Exception as e:
                print(f"  ❌ Error guardando KB{kb}: {e}")

    print(f"\n{'='*50}")
    print(f"Sincronización completada. Nuevos registros GDR: {nuevos}")
    return nuevos
