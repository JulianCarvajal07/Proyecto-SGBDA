import requests
from datetime import datetime
from sgbda.models import actualizaciones
import re
from bs4 import BeautifulSoup


def sync_gdr():
    print("Iniciando sincronización GDR...")

    # ── SQL Server ────────────────────────────────────────────────────────────
    URLS_SQL = {
        "2014": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2014/build-versions.md",
        "2016": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2016/build-versions.md",
        "2017": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2017/build-versions.md",
        "2019": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2019/build-versions.md",
        "2022": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2022/build-versions.md",
        "2025": "https://raw.githubusercontent.com/MicrosoftDocs/SupportArticles-docs/main/support/sql/releases/sqlserver-2025/build-versions.md",
    }

    FORMATOS_FECHA = ["%B %d, %Y", "%Y-%m-%d", "%d/%m/%Y"]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    nuevos = 0

    # ── Helpers SQL Server ────────────────────────────────────────────────────

    def es_gdr(descripcion):
        desc = descripcion.upper().strip()
        desc = re.sub(r'^SQL\s+SERVER\s+\d{4}\s+', '', desc)
        return bool(
            re.match(
                r'^(SP\d+\s+CU\d+\s*\+\s*GDR|SP\d+\s*\+\s*GDR|CU\d+\s*\+\s*GDR|SP\d+\s+GDR|MS\d{2}-\d{3}:\s*GDR\s*SECURITY\s*UPDATE)$',
                desc
            )
        )

    def parsear_fila(cols, version):
        if version in ("2014", "2016"):
            if len(cols) < 4:
                return None
            return cols[0], cols[1], cols[2], cols[3]
        else:
            if len(cols) < 7:
                return None
            return cols[0], cols[1], cols[5], cols[6]

    # ── Sincronización SQL Server ─────────────────────────────────────────────

    for version, url in URLS_SQL.items():
        print(f"\nProcesando SQL Server {version}...")

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  ⚠️  Error de red: {e}")
            continue

        for linea in response.text.splitlines():
            if not linea.startswith("|"):
                continue
            if re.match(r'^\s*\|[\s\-:]+\|', linea):
                continue

            cols = [c.strip() for c in linea.strip("|").split("|")]
            cols = [re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', c) for c in cols]
            cols = [re.sub(r'\*\*([^*]+)\*\*', r'\1', c) for c in cols]

            resultado = parsear_fila(cols, version)
            if not resultado:
                continue

            descripcion, build, kb_raw, fecha_raw = resultado

            if re.search(
                r'(?i)cumulative update name|gdr name|sp name|build version|product version|knowledge base|release date',
                descripcion
            ):
                continue

            if not es_gdr(descripcion):
                continue

            kb = re.sub(r'(?i)^kb', '', kb_raw).strip()

            fecha_obj = None
            for fmt in FORMATOS_FECHA:
                try:
                    fecha_obj = datetime.strptime(fecha_raw.strip(), fmt).date()
                    break
                except ValueError:
                    continue

            if not kb or not build:
                continue

            print(f"  ✅ [SQL {version}] {descripcion} | Build: {build} | KB: {kb} | Fecha: {fecha_obj}")

            try:
                obj, created = actualizaciones.objects.update_or_create(
                    kb=kb,
                    defaults={
                        "motor":         "SQL SERVER",
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

    # ── Sincronización PostgreSQL vía API endoflife.date ─────────────────────────

    PG_VERSIONS_SOPORTADAS = {"14", "15", "16", "17", "18"}
    PG_EOL_API = "https://endoflife.date/api/postgresql.json"

    print("\n" + "=" * 50)
    print("Iniciando sincronización PostgreSQL...")

    try:
        resp = requests.get(PG_EOL_API, headers=headers, timeout=15)
        resp.raise_for_status()
        pg_data = resp.json()
    except requests.RequestException as e:
        print(f"  ⚠️  Error consultando API PostgreSQL: {e}")
        pg_data = []

    # La API devuelve una lista de releases con esta estructura:
    # {
    #   "cycle": "17",
    #   "releaseDate": "2024-09-26",
    #   "eol": "2029-11-08",
    #   "latest": "17.9",
    #   "latestReleaseDate": "2026-02-26",
    #   "lts": false,
    #   "support": true
    # }

    for release in pg_data:
        major = str(release.get("cycle", ""))

        if major not in PG_VERSIONS_SOPORTADAS:
            continue

        version       = release.get("latest", "")          # ej: "17.9"
        fecha_raw     = release.get("latestReleaseDate", "") # ej: "2026-02-26"
        eol_raw       = release.get("eol", "")
        soportado     = release.get("support", False)

        fecha_obj = None
        try:
            fecha_obj = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass

        descripcion = f"Minor Release {version}"
        kb_pg       = f"PG-{version}"

        print(f"  ✅ [PG {major}] {version} | Fecha: {fecha_obj} | Soportado: {soportado}")

        try:
            obj, created = actualizaciones.objects.update_or_create(
                kb=kb_pg,
                defaults={
                    "major_version": major,
                    "build":         version,
                    "descripcion":   descripcion,
                    "release_date":  fecha_obj,
                    "soportado":     soportado,
                }
            )
            if created:
                nuevos += 1
        except Exception as e:
            print(f"  ❌ Error guardando PG {version}: {e}")