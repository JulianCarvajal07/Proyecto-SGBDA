# reportes/services.py
import json
import paramiko
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls



PROCESOS_CLAVE = ['pmon', 'smon', 'lgwr', 'dbwr', 'ckpt', 'tnslsnr', 'reco', 'mmon']

# Lista de posibles rutas donde puede estar el script
RUTAS_CANDIDATAS = [
    "/oracle/app/oracle/scripts/extraer_metricas_json.sh",
    "/oracle/scripts/extraer_metricas_json.sh",
    "/u01/app/oracle/scripts/extraer_metricas_json.sh",
    "/home/oracle/scripts/extraer_metricas_json.sh",
    "/opt/oracle/scripts/extraer_metricas_json.sh",
]

# =================================================================================== #
# =================================================================================== #
# =================================================================================== #
# =================================================================================== #

def detectar_script(ssh, rutas):
    """Devuelve la primera ruta que exista en el servidor remoto."""
    for ruta in rutas:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {ruta} && echo 'EXISTS' || echo 'MISSING'")
        resultado = stdout.read().decode('utf-8').strip()
        if resultado == "EXISTS":
            return ruta
    return None

# =================================================================================== #
# =================================================================================== #
# =================================================================================== #
# =================================================================================== #

def filtrar_procesos_clave(procesos):
    return [p for p in procesos if any(clave in p.lower() for clave in PROCESOS_CLAVE)]

# =================================================================================== #
# =================================================================================== #
# =================================================================================== #
# =================================================================================== #

def parsear_procesos(lineas):
    procesos = []
    for linea in lineas:
        partes = linea.split(None, 7)  # separa por espacios, máx 8 columnas
        if len(partes) >= 8:
            procesos.append({
                'usuario': partes[0],
                'pid': partes[1],
                'inicio': partes[4],
                'cpu_time': partes[6],
                'comando': partes[7],
            })
    return procesos

# =================================================================================== #
# =================================================================================== #
# =================================================================================== #
# =================================================================================== #

def obtener_metricas_oracle(host, puerto, user, password):
    """Conecta vía SSH usando los parámetros dinámicos de la BD."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Conexión SSH con los datos dinámicos recibidos
    ssh.connect(
        hostname=host,
        port=puerto, 
        username=user, 
        password=password, 
        timeout=10
    )

    # 1. Detectar qué script existe
    script_remoto = detectar_script(ssh, RUTAS_CANDIDATAS)
    
    if not script_remoto:
        ssh.close()
        raise Exception("No se encontró el script extraer_metricas_json.sh en ninguna ruta conocida.")

    
    comando = f"bash -l {script_remoto} >/dev/null 2>&1 && cat /tmp/metricas_oracle.json"
    stdin, stdout, stderr = ssh.exec_command(comando)
    salida_texto = stdout.read().decode('utf-8').strip()
    salida_error = stderr.read().decode('utf-8').strip()
    ssh.close()

    # Si hay errores en stderr, lanzamos la excepción con ese mensaje
    if salida_error and not salida_texto:
        raise Exception(f"Error en script SSH: {salida_error}")
        
    try:
        datos = json.loads(salida_texto)
    except json.JSONDecodeError:
        # Esto te mostrará en pantalla qué texto extraño devolvió el servidor en vez de JSON
        raise Exception(f"Salida no válida recibida del servidor:\n'{salida_texto}'")

    # Procesar la lista de procesos: filtrar solo los clave y parsearlos a dict
    procesos_raw = datos.get('procesos_oracle', [])
    procesos_filtrados = filtrar_procesos_clave(procesos_raw)
    datos['procesos_oracle_clave'] = parsear_procesos(procesos_filtrados)

    return datos

# =================================================================================== #
# =================================================================================== #
# =================================================================================== #
# =================================================================================== #

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

# =================================================================================== #
# =================================================================================== #
# =================================================================================== #
# =================================================================================== #




