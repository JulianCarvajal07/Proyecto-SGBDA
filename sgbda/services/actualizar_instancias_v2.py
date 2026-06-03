import pyodbc
from sgbda.models import conexion, instancia, servidor, servicio


# ─── Conexión ────────────────────────────────────────────────────────────────

def conectar_sqlserver(ip, puerto, usuario, password):
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={ip},{puerto};"
        f"UID={usuario};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=60;"
    )
    return pyodbc.connect(conn_str)


def conectar_postgresql(ip, puerto, usuario, password):
    conn_str = (
        "DRIVER={PostgreSQL Unicode};"  # o {PostgreSQL ANSI} según el driver instalado
        f"SERVER={ip};"
        f"PORT={puerto};"
        f"UID={usuario};"
        f"PWD={password};"
        "DATABASE=postgres;"
        "TrustServerCertificate=yes;"
        "Trusted_Connection=no;"
    )
    return pyodbc.connect(conn_str)


# ─── Procesadores por motor ──────────────────────────────────────────────────

def procesar_sqlserver(c, nuevos_servidores, nuevas_instancias, errores):
    conn = None
    cursor = None

    try:
        print(f"Conectando a {c.ip_servidor}...")

        conn = conectar_sqlserver(
            c.ip_servidor,
            c.puerto,
            c.usuario,
            c.password_encriptado
        )

        cursor = conn.cursor()

        print(f"Consultando metadata en {c.ip_servidor}...")

        # PRIMERA CONSULTA
        print("Ejecutando metadata...")
        cursor.execute("""
            DECLARE @version VARCHAR(MAX);
            SET @version = @@VERSION;

            SELECT
                CAST(SERVERPROPERTY('MachineName') AS NVARCHAR(200)),
                CAST(CONNECTIONPROPERTY('local_tcp_port') AS INT),
                CAST(LEFT(@version, CHARINDEX('(', @version + '(') - 2) AS NVARCHAR(128)),
                CAST(SERVERPROPERTY('Edition') AS NVARCHAR(128)),
                CAST(REPLACE(REPLACE(servicename, 'SQL Server (',''), ')','') AS NVARCHAR(128)),
                CAST(SUBSTRING(@version,
                    CHARINDEX(' - ', @version) + 3,
                    CHARINDEX('(X64)', @version) - CHARINDEX(' - ', @version) - 4
                ) AS NVARCHAR(128)),
                CAST(LTRIM(RTRIM(
                    SUBSTRING(
                        @version,
                        CHARINDEX('Windows', @version),
                        CHARINDEX('(Build', @version) - CHARINDEX('Windows', @version)
                    )
                )) AS NVARCHAR(128))
            FROM sys.dm_server_services
            WHERE servicename LIKE 'SQL Server (%';
        """)
        print("Metadata OK")

        row = cursor.fetchone()

        if not row:
            errores.append(f"Sin datos de metadata en {c.ip_servidor}")
            return nuevos_servidores, nuevas_instancias

        hostname, puerto_sql, version, edition, nombre_instancia, build, sistema_op = row

        srv, created_srv = servidor.objects.update_or_create(
            ip=c.ip_servidor,
            defaults={
                "hostname": hostname or c.ip_servidor,
                "sistema_operativo": sistema_op
            }
        )

        if created_srv:
            nuevos_servidores += 1

        inst, created_inst = instancia.objects.update_or_create(
            servidor=srv,
            nombre_instancia=nombre_instancia,
            defaults={
                "major_version": version,
                "edition": edition,
                "build": build,
                "puerto": puerto_sql or c.puerto,
            }
        )

        if created_inst:
            nuevas_instancias += 1

        print(f"Metadata OK en {c.ip_servidor}")

        # SEGUNDA CONSULTA
        print(f"Consultando servicios vía xp_cmdshell en {c.ip_servidor}...")

        try:
            print("Ejecutando xp_cmdshell...")
            cursor.execute("""
                EXEC xp_cmdshell '
                powershell.exe -Command
                "Get-Service |
                 Where-Object {$_.DisplayName -like ''*SQL*''} |
                 ForEach-Object {
                    $_.DisplayName + ''|'' +
                    $_.Status + ''|'' +
                    $_.StartType
                 }"
                '
            """)
            print("xp_cmdshell OK")

            for row in cursor.fetchall():

                if not row or not row[0]:
                    continue

                datos = row[0].split("|")

                if len(datos) != 3:
                    continue

                nombre, estado, inicio = [x.strip() for x in datos]

                servicio.objects.update_or_create(
                    instancia=inst,
                    nombre_servicio=nombre,
                    defaults={
                        "estado_servicio": estado,
                        "tipo_inicio": inicio
                    }
                )

            print(f"Servicios OK en {c.ip_servidor}")

        except Exception as e:
            errores.append(
                f"Error obteniendo servicios en {c.ip_servidor}: {e}"
            )
            print(
                f"Error obteniendo servicios en {c.ip_servidor}: {e}"
            )

    except Exception as e:

        errores.append(
            f"Error obteniendo metadata en {c.ip_servidor}: {e}"
        )

        print(
            f"Error obteniendo metadata en {c.ip_servidor}: {e}"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return nuevos_servidores, nuevas_instancias


def procesar_postgresql(c, nuevos_servidores, nuevas_instancias, errores):
    conn = None
    cursor = None
    try:
        conn = conectar_postgresql(c.ip_servidor, c.puerto, c.usuario, c.password_encriptado)
        cursor = conn.cursor()

        # Metadata del servidor: versión, nombre de instancia (cluster), SO, etc.
        cursor.execute("""
            SELECT
                inet_server_addr()::TEXT,
                       
                inet_server_port(),
                       
                current_setting('server_version'),
                
                'PostgreSQL ' || substring(current_setting('server_version') from '^[0-9]+') AS postgres_version,
                       
                (
                    regexp_match(
                        pg_read_file('/etc/os-release'),
                        'PRETTY_NAME="([^"]+)"'
                    )
                )[1] AS sistema_operativo,

                (SELECT setting FROM pg_settings WHERE name = 'cluster_name'),
                       
                (SELECT setting FROM pg_settings WHERE name = 'data_directory')
        """)

        row = cursor.fetchone()
        if not row:
            errores.append(f"Sin datos de metadata en {c.ip_servidor} (PostgreSQL)")
            return nuevos_servidores, nuevas_instancias

        ip_srv, puerto_pg, version_corta, major_version, sistema_ope, cluster_name, data_dir = row

        # Normalizar nombre de instancia: usar cluster_name si existe, si no el puerto
        nombre_instancia = cluster_name if cluster_name else f"postgres:{puerto_pg or c.puerto}"

        # Extraer edición/variante desde la cadena completa de version()
        # Ej: "PostgreSQL 16.2 on x86_64-pc-linux-gnu, compiled by gcc..."
        edition = "PostgreSQL"

        srv, created_srv = servidor.objects.update_or_create(
            ip=c.ip_servidor,
            defaults={
                "hostname": ip_srv or c.ip_servidor, 
                "sistema_operativo": sistema_ope
            }
        )
        if created_srv:
            nuevos_servidores += 1

        inst, created_inst = instancia.objects.update_or_create(
            servidor=srv,
            nombre_instancia=nombre_instancia,
            defaults={
                "major_version": major_version,
                "edition": edition,
                "build": version_corta,   # cadena completa como build
                "puerto": puerto_pg or c.puerto,
            }
        )
        if created_inst:
            nuevas_instancias += 1

        print(f"OK (PostgreSQL) {c.ip_servidor} → {nombre_instancia}")

        # Servicios: pg_stat_activity da info de backends activos como proxy de servicios
        cursor.execute("""
            SELECT
                datname         AS nombre_servicio,
                state           AS estado_servicio,
                'automatic'     AS tipo_inicio
            FROM pg_stat_activity
            WHERE datname IS NOT NULL
            GROUP BY datname, state
            ORDER BY datname;
        """)

        for svc_row in cursor.fetchall():
            nombre, estado, inicio = svc_row
            servicio.objects.update_or_create(
                instancia=inst,
                nombre_servicio=nombre,
                defaults={"estado_servicio": estado or "unknown", "tipo_inicio": inicio}
            )

    except Exception as e:
        errores.append(f"Error con {c.ip_servidor} (PostgreSQL): {e}")
        print(f"Error con {c.ip_servidor}: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return nuevos_servidores, nuevas_instancias


# ─── Despachador principal ───────────────────────────────────────────────────

MOTORES = {
    "sqlserver":  procesar_sqlserver,
    "postgresql": procesar_postgresql,
}

def normalizar_motor(motor):
    m = (motor or "").lower().strip()
    if m in ("sql server", "sqlserver", "mssql"):
        return "sqlserver"
    if m in ("postgresql", "postgres", "pg"):
        return "postgresql"
    return m


def actualizar_instancias_desde_conexiones():
    conexiones = conexion.objects.all()

    nuevos_servidores = 0
    nuevas_instancias = 0
    errores = []

    for c in conexiones:
        motor = normalizar_motor(c.motor)
        procesador = MOTORES.get(motor)

        if procesador is None:
            msg = f"Motor desconocido '{c.motor}' en conexión {c.ip_servidor} — omitido."
            errores.append(msg)
            print(msg)
            continue

        nuevos_servidores, nuevas_instancias = procesador(
            c, nuevos_servidores, nuevas_instancias, errores
        )

    return {
        "servidores_nuevos": nuevos_servidores,
        "instancias_nuevas": nuevas_instancias,
        "errores": errores,
    }