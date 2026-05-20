import pyodbc
from sgbda.models import conexion, instancia, servidor 


def conectar_sqlserver(ip, puerto, usuario, password):

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={ip},{puerto};"
        f"UID={usuario};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(conn_str)


def actualizar_instancias_desde_conexiones():

    conexiones = conexion.objects.all()

    nuevos_servidores = 0
    nuevas_instancias = 0

    for c in conexiones:

        try:
            conn = conectar_sqlserver(
                c.ip_servidor,
                c.puerto,
                c.usuario,
                c.password_encriptado  # ⚠️ aquí debes desencriptar
            )

            cursor = conn.cursor()

            # 🧠 metadata del servidor + instancia
            cursor.execute("""
                SELECT
                    CAST(@@SERVERNAME AS NVARCHAR(128)),
                    CAST(SERVERPROPERTY('MachineName') AS NVARCHAR(128)),
                    CAST(SERVERPROPERTY('Edition') AS NVARCHAR(128)),
                    CAST(SERVERPROPERTY('ProductVersion') AS NVARCHAR(128)),
                    CAST(CONNECTIONPROPERTY('local_tcp_port') AS INT)
            """)

            row = cursor.fetchone()

            if not row:
                continue

            nombre_instancia, hostname, edition, version, puerto_sql = row

            # 🖥️ 1. CREAR / ACTUALIZAR SERVIDOR
            srv, created_srv = servidor.objects.update_or_create(

                ip=c.ip_servidor,

                defaults={
                    "hostname": hostname or c.ip_servidor,
                    "sistema_operativo": "Desconocido",  # opcional
                }
            )

            if created_srv:
                nuevos_servidores += 1

            # 🗄️ 2. CREAR / ACTUALIZAR INSTANCIA
            inst, created_inst = instancia.objects.update_or_create(

                servidor=srv,

                nombre_instancia=nombre_instancia,

                defaults={
                    "major_version": version,
                    "edition": edition,
                    "puerto": puerto_sql or c.puerto,
                }
            )

            if created_inst:
                nuevas_instancias += 1

            print(f"OK {c.ip_servidor} → {nombre_instancia}")

        except Exception as e:
            print(f"Error con {c.ip_servidor}: {e}")

    return {
        "servidores_nuevos": nuevos_servidores,
        "instancias_nuevas": nuevas_instancias
    }