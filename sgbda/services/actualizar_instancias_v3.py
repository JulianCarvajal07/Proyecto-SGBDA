import time
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
        "Network Packet Size=4096;"
    )
    conn = pyodbc.connect(conn_str)
    conn.timeout = 30
    return conn


def conectar_postgresql(ip, puerto, usuario, password):
    conn_str = (
        "DRIVER={PostgreSQL Unicode};"
        f"SERVER={ip};"
        f"PORT={puerto};"
        f"UID={usuario};"
        f"PWD={password};"
        "DATABASE=postgres;"
        "TrustServerCertificate=yes;"
        "Trusted_Connection=no;"
    )
    return pyodbc.connect(conn_str)


# ─── Utilidad de reintentos ──────────────────────────────────────────────────

def conectar_con_reintentos(fn_conectar, ip, puerto, usuario, password, max_intentos=4, pausa=3):
    ultimo_error = None

    for intento in range(1, max_intentos + 1):
        try:
            print(f"  Intento {intento}/{max_intentos} conectando a {ip}...")
            conn = fn_conectar(ip, puerto, usuario, password)
            print(f"  Conexión establecida en intento {intento}")
            return conn

        except Exception as e:
            ultimo_error = e
            print(f"  Intento {intento} fallido en {ip}: {e}")

            if intento < max_intentos:
                espera = pausa * intento  # 3s, 6s, 9s
                print(f"  Esperando {espera}s antes del siguiente intento...")
                time.sleep(espera)

    raise ultimo_error


# ─── Procesadores por motor ──────────────────────────────────────────────────

def procesar_sqlserver(c, nuevos_servidores, nuevas_instancias, errores, log):

    # ── FASE 1: Metadata ─────────────────────────────────────────────────────
    conn = None
    cursor = None
    inst = None

    try:
        log(f"Conectando a {c.ip_servidor}...")
        conn = conectar_con_reintentos(
            conectar_sqlserver,
            c.ip_servidor, c.puerto, c.usuario, c.password_encriptado
        )
        cursor = conn.cursor()

        log(f"Consultando metadata en {c.ip_servidor}...")
        log("Ejecutando metadata...")

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
        log("Metadata OK")

        row = cursor.fetchone()

        if not row:
            errores.append(f"Sin datos de metadata en {c.ip_servidor}")
            return nuevos_servidores, nuevas_instancias

        hostname, puerto_sql, version, edition, nombre_instancia, build, sistema_op = row

    except Exception as e:
        errores.append(f"Error obteniendo metadata en {c.ip_servidor}: {e}")
        log(f"Error obteniendo metadata en {c.ip_servidor}: {e}")
        return nuevos_servidores, nuevas_instancias

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # ── ORM fuera de la conexión ─────────────────────────────────────────────
    try:
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

        log(f"Metadata OK en {c.ip_servidor}")

    except Exception as e:
        errores.append(f"Error guardando metadata de {c.ip_servidor}: {e}")
        log(f"Error guardando metadata de {c.ip_servidor}: {e}")
        return nuevos_servidores, nuevas_instancias

# ── FASE 2: Servicios ────────────────────────────────────────────────────
    conn = None
    cursor = None
    ultimo_error_servicios = None

    for intento in range(1, 5):
        conn = None
        cursor = None
        try:
            log(f"  Intento {intento}/4 obteniendo servicios en {c.ip_servidor}...")
            conn = conectar_con_reintentos(
                conectar_sqlserver,
                c.ip_servidor, c.puerto, c.usuario, c.password_encriptado
            )
            cursor = conn.cursor()

            inicio = time.time()
            #NOTA: Esta consulta SQL debe dejarse en una sola linea para ejecutarse correctamente
            cursor.execute("""
                EXEC xp_cmdshell 'powershell.exe -Command "Get-Service -Name ''SQL*'',''MSSQL*'',''MSDTS*'' | ForEach-Object {$_.DisplayName + ''|'' + $_.Status + ''|'' + $_.StartType}"'
            """)
            log(f"Tiempo consulta xp_cmdshell: {time.time() - inicio:.2f} segundos")
            log("xp_cmdshell OK")

            for row in cursor.fetchall():
                if not row or not row[0]:
                    continue
                datos = row[0].split("|")
                if len(datos) != 3:
                    continue
                nombre, estado, tipo_inicio = [x.strip() for x in datos]
                servicio.objects.update_or_create(
                    instancia=inst,
                    nombre_servicio=nombre,
                    defaults={
                        "estado_servicio": estado,
                        "tipo_inicio": tipo_inicio
                    }
                )

            log(f"Servicios OK en {c.ip_servidor}")
            break  # éxito, salir del loop

        except Exception as e:
            ultimo_error_servicios = e
            log(f"  Intento {intento} fallido obteniendo servicios en {c.ip_servidor}: {e}")

            if intento < 4:
                espera = 3 * intento  # 3s, 6s, 9s
                log(f"  Esperando {espera}s antes del siguiente intento...")
                time.sleep(espera)

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    else:
        # Se agotaron los 4 intentos sin un break exitoso
        errores.append(f"Error obteniendo servicios en {c.ip_servidor} (4 intentos agotados): {ultimo_error_servicios}")
        log(f"Error obteniendo servicios en {c.ip_servidor}: {ultimo_error_servicios}")

    return nuevos_servidores, nuevas_instancias


def procesar_postgresql(c, nuevos_servidores, nuevas_instancias, errores, log):

    # ── FASE 1: Metadata ─────────────────────────────────────────────────────
    conn = None
    cursor = None

    try:
        conn = conectar_con_reintentos(
            conectar_postgresql,
            c.ip_servidor, c.puerto, c.usuario, c.password_encriptado
        )
        cursor = conn.cursor()

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

    except Exception as e:
        errores.append(f"Error obteniendo metadata en {c.ip_servidor} (PostgreSQL): {e}")
        log(f"Error con {c.ip_servidor}: {e}")
        return nuevos_servidores, nuevas_instancias

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # ── ORM fuera de la conexión ─────────────────────────────────────────────
    try:
        nombre_instancia = cluster_name if cluster_name else f"postgres:{puerto_pg or c.puerto}"
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
                "build": version_corta,
                "puerto": puerto_pg or c.puerto,
            }
        )

        if created_inst:
            nuevas_instancias += 1

        log(f"OK (PostgreSQL) {c.ip_servidor} → {nombre_instancia}")

    except Exception as e:
        errores.append(f"Error guardando metadata de {c.ip_servidor} (PostgreSQL): {e}")
        log(f"Error guardando metadata de {c.ip_servidor}: {e}")
        return nuevos_servidores, nuevas_instancias

    # ── FASE 2: Servicios ────────────────────────────────────────────────────
    conn = None
    cursor = None

    try:
        conn = conectar_con_reintentos(
            conectar_postgresql,
            c.ip_servidor, c.puerto, c.usuario, c.password_encriptado
        )
        cursor = conn.cursor()

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
            nombre, estado, tipo_inicio = svc_row
            servicio.objects.update_or_create(
                instancia=inst,
                nombre_servicio=nombre,
                defaults={
                    "estado_servicio": estado or "unknown",
                    "tipo_inicio": tipo_inicio
                }
            )

        log(f"Servicios OK en {c.ip_servidor}")

    except Exception as e:
        errores.append(f"Error obteniendo servicios en {c.ip_servidor} (PostgreSQL): {e}")
        log(f"Error obteniendo servicios en {c.ip_servidor}: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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


def actualizar_instancias_desde_conexiones(log_queue=None):

    def log(msg):
        print(msg)
        if log_queue:
            log_queue.put(msg)

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
            log(msg)
            continue

        nuevos_servidores, nuevas_instancias = procesador(
            c, nuevos_servidores, nuevas_instancias, errores, log
        )

    log(f"✔ Finalizado — Servidores nuevos: {nuevos_servidores} | Instancias nuevas: {nuevas_instancias}")

    if errores:
        for e in errores:
            log(f"✘ {e}")

    return {
        "servidores_nuevos": nuevos_servidores,
        "instancias_nuevas": nuevas_instancias,
        "errores": errores,
    }