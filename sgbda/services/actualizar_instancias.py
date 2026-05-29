import pyodbc
from sgbda.models import conexion, instancia, servidor, servicio


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
    errores=[]

    for c in conexiones:

        cursor = None  # ✅ inicializar aquí
        conn = None    # ✅ inicializar aquí

        try:
            conn = conectar_sqlserver(
                c.ip_servidor,
                c.puerto,
                c.usuario,
                c.password_encriptado 
            )

            cursor = conn.cursor()

            #🧠 metadata del servidor + instancia
            cursor.execute("""
                DECLARE @version VARCHAR(MAX);

                SET @version = @@VERSION;

                SELECT
                    CAST(@@SERVERNAME AS NVARCHAR(128)),
                           
                    CAST(CONNECTIONPROPERTY('local_tcp_port') AS INT),

                    -- Version SQL limpia
                    CAST(LEFT(@version, CHARINDEX('(', @version + '(') - 2) AS NVARCHAR(128)),

                    -- Edición SQL
                    CAST(SERVERPROPERTY('Edition') AS NVARCHAR(128)),

                    -- Instancia
                    CAST(REPLACE(REPLACE(servicename, 'SQL Server (',''), ')','') AS NVARCHAR(128)),

                    -- Build
                    CAST(SUBSTRING(@version, CHARINDEX(' - ', @version) + 3, CHARINDEX('(X64)', @version) - CHARINDEX(' - ', @version) - 4) AS NVARCHAR(128)),

                    -- Sistema Operativo
                    CAST(LTRIM(RTRIM(
                        SUBSTRING(
                            @version,
                            CHARINDEX('Windows', @version),
                            CHARINDEX('(Build', @version) - CHARINDEX('Windows', @version)
                        )
                    )) AS NVARCHAR(128))

                FROM sys.dm_server_services
                WHERE servicename LIKE 'SQL Server (%';
                           
                EXEC xp_cmdshell 'powershell.exe -Command "Get-Service | Where-Object {$_.DisplayName -like ''*SQL*''} | ForEach-Object { $_.DisplayName, $_.Status, $_.StartType -join ''|'' }"';
            """)

            # Primer resultset (metadata)
            row = cursor.fetchone()

            if row:
                
                hostname = row[0]
                puerto_sql = row[1]
                version = row[2]
                edition = row[3]
                nombre_instancia = row[4]
                build = row[5]
                sistema_op = row[6]



            # 🖥️ 1. CREAR / ACTUALIZAR SERVIDOR
            srv, created_srv = servidor.objects.update_or_create(

                ip=c.ip_servidor,

                defaults={
                    "hostname": hostname or c.ip_servidor,
                    "sistema_operativo": sistema_op,  # opcional
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
                    "build": build,
                    "puerto": puerto_sql or c.puerto,
                }
            )

            if created_inst:
                nuevas_instancias += 1

            print(f"OK {c.ip_servidor} → {nombre_instancia}")

            
            if cursor.nextset():
                rows = cursor.fetchall()
                for row in rows:
                    if row and row[0]:

                        datos = row[0].split("|")

                        if len(datos) == 3:

                            nombre = datos[0].strip()
                            estado = datos[1].strip()
                            inicio = datos[2].strip()

                            print(nombre)
                            print(estado)
                            print(inicio)

                            servicio.objects.update_or_create(
                                instancia=inst,
                                nombre_servicio=nombre,
                                defaults={
                                    "estado_servicio": estado,
                                    "tipo_inicio": inicio
                                }
                            )
            else:
                print("No hay segundo resultset")
            

        except Exception as e:
            errores.append(f"Error con {c.ip_servidor}: {e}")  # ✅ ahora sí captura el error real             
            print(f"Error con {c.ip_servidor}: {e}")
        finally:
            # cerrar cursor
            if cursor:
                cursor.close()

            # cerrar conexión
            if conn:
                conn.close()

    return {
        "servidores_nuevos": nuevos_servidores,
        "instancias_nuevas": nuevas_instancias,
        "errores":errores
    }