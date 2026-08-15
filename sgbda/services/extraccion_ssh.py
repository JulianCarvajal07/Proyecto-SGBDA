# reportes/services.py
import json
import os
import paramiko
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from django.conf import settings
from docx import Document

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

# ============================================================
# CREACION DE DOCUMENTO WORD
# ============================================================
def generar_reporte_oracle(datos, buffer=None, ruta_salida="/tmp/reporte_oracle.docx",
                           empresa=None, conexion=None):
    """
    Genera un reporte Word (.docx) con las métricas de Oracle.
    
    Args:
        datos_json: dict con la estructura del JSON de métricas
        buffer: BytesIO opcional. Si se pasa, guarda ahí (para descarga web).
        ruta_salida: str opcional. Ruta del archivo si no se pasa buffer.
    """
    # ============================================================
    # ABRIR PLANTILLA
    # ============================================================
    if not os.path.exists(settings.PLANTILLA_WORD_PATH):
        raise FileNotFoundError(f"No existe la plantilla: {settings.PLANTILLA_WORD_PATH}")
    
    doc = Document(settings.PLANTILLA_WORD_PATH)
    
    # ============================================================
    # CONFIGURAR PÁGINA
    # ============================================================
    section = doc.sections[0]
    section.page_height = Cm(27.94)
    section.page_width = Cm(21.59)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    
    # ============================================================
    # FUNCIONES AUXILIARES
    # ============================================================
    def parrafo_vacio(espacio_pt=12):
        p = doc.add_paragraph()
        p.space_after = Pt(espacio_pt)
        return p



    def texto_posicionado(doc, texto, posicion='centro', tamano=11, bold=False,
                        color=(64,64,64), fuente='Calibri'):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # ─────────────────────────────────────────
        # ESPACIO ARRIBA (antes del texto)
        # Aumentá o disminuí este número para subir/bajar el texto
        # ─────────────────────────────────────────
        p.paragraph_format.space_before = Pt(0)   # ← 0 = sin espacio arriba

        # ─────────────────────────────────────────
        # TEXTO
        # ─────────────────────────────────────────
        run = p.add_run(texto)
        run.font.size = Pt(tamano)
        run.font.name = fuente
        run.bold = bold
        run.font.color.rgb = RGBColor(*color)

        # ─────────────────────────────────────────
        # ESPACIO ABAJO (después del texto)
        # Aumentá o disminuí este número para separar más/menos del siguiente elemento
        # ─────────────────────────────────────────
        p.paragraph_format.space_after = Pt(0)    # ← 0 = sin espacio abajo

        return p

    def texto_centrado(texto, tamano=11, bold=True, color=(64,64,64), fuente='Calibri', espacio_despues=6):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(texto)
        run.font.size = Pt(tamano)
        run.font.name = fuente
        run.bold = bold
        run.font.color.rgb = RGBColor(*color)
        p.space_after = Pt(espacio_despues)
        return p

    def tabla_sin_bordes(filas, col_widths, alineacion_col1=WD_ALIGN_PARAGRAPH.RIGHT):
        """filas: lista de [texto_col1, texto_col2]"""
        table = doc.add_table(rows=0, cols=2)
        table.autofit = False
        table.allow_autofit = False
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Quitar bordes globales de la tabla
        tbl = table._tbl
        tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'nil')
            border.set(qn('w:sz'), '0')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'auto')
            tblBorders.append(border)
        tblPr.append(tblBorders)
        
        for fila in filas:
            row = table.add_row().cells
            row[0].text = fila[0]
            row[1].text = fila[1]
            
            row[0].width = col_widths[0]
            row[1].width = col_widths[1]
            
            # Formato col 1 (título)
            for paragraph in row[0].paragraphs:
                paragraph.alignment = alineacion_col1
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(12)
                    run.font.name = 'Calibri'
                    run.font.color.rgb = RGBColor(80, 80, 80)
            
            # Formato col 2 (valor)
            for paragraph in row[1].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    run.font.size = Pt(12)
                    run.font.name = 'Calibri'
                    run.font.color.rgb = RGBColor(64, 64, 64)
            
            # Quitar bordes de celdas individualmente
            for cell in row:
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcBorders = OxmlElement('w:tcBorders')
                for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                    border = OxmlElement(f'w:{border_name}')
                    border.set(qn('w:val'), 'nil')
                    border.set(qn('w:sz'), '0')
                    border.set(qn('w:space'), '0')
                    border.set(qn('w:color'), 'auto')
                    tcBorders.append(border)
                tcPr.append(tcBorders)
        
        return table

    def agregar_titulo(texto, nivel=1, centrado=False):
        p = doc.add_heading(texto, level=nivel)
        if centrado:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return p

    def formatear_celda_contenido(cell, texto, alineacion_horizontal=WD_ALIGN_PARAGRAPH.LEFT):
        cell.text = texto
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        
        for paragraph in cell.paragraphs:
            paragraph.alignment = alineacion_horizontal
            # Espaciado simétrico para centrar verticalmente el texto
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(4)
            
            for run in paragraph.runs:
                run.font.size = Pt(12)
                run.font.name = 'Calibri'
                run.font.color.rgb = RGBColor(64, 64, 64)

    def agregar_tabla_contenidos(doc, items):
        """
        items: lista de tuplas [(titulo, numero_pagina), ...]
        Ejemplo: [("1. Resumen Ejecutivo", "3"), ("2. Estado del Servidor", "3")]
        """
        # Separación 2: otro párrafo vacío (Word nunca colapsa dos seguidos con contenido)
        sep2 = doc.add_paragraph()
        sep2.add_run(' ')
        sep2.paragraph_format.space_after = Pt(4)

        # Título "Contenido"
        p = doc.add_paragraph()
        run = p.add_run("Contenido")
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(0, 0, 0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(12)

        # Separación 1: párrafo vacío con run invisible
        sep1 = doc.add_paragraph()
        sep1.add_run(' ')
        sep1.paragraph_format.space_after = Pt(10)

        # Tabla sin bordes visibles
        table = doc.add_table(rows=0, cols=2)
        table.autofit = False
        table.allow_autofit = False
        
        # Ancho total de la tabla (ajusta a tus márgenes)
        table.width = Cm(17)
        
        for titulo, pagina in items:
            row = table.add_row().cells
            
            row[0].width = Cm(14)
            row[1].width = Cm(3)
            
            # Formatear celdas con centrado vertical
            formatear_celda_contenido(row[0], titulo, WD_ALIGN_PARAGRAPH.LEFT)
            formatear_celda_contenido(row[1], str(pagina), WD_ALIGN_PARAGRAPH.RIGHT)
            
            # Altura de fila
            tr = row[0]._tc.getparent()
            trPr = tr.get_or_add_trPr()
            trHeight = OxmlElement('w:trHeight')
            trHeight.set(qn('w:val'), '500')
            trHeight.set(qn('w:hRule'), 'atLeast')
            trPr.append(trHeight)
            
            # Bordes solo abajo
            for cell in row:
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcBorders = OxmlElement('w:tcBorders')
                for border_name in ['top', 'left', 'right', 'insideH', 'insideV']:
                    border = OxmlElement(f'w:{border_name}')
                    border.set(qn('w:val'), 'nil')
                    border.set(qn('w:sz'), '0')
                    tcBorders.append(border)
                
                bottom = OxmlElement('w:bottom')
                bottom.set(qn('w:val'), 'single')
                bottom.set(qn('w:sz'), '4')
                bottom.set(qn('w:color'), 'BFBFBF')
                tcBorders.append(bottom)
                tcPr.append(tcBorders)

        doc.add_paragraph()
    
    def agregar_parrafo(texto, negrita=False, centrado=False, tamano=11, color=None):
        p = doc.add_paragraph()
        run = p.add_run(texto)
        run.font.size = Pt(tamano)
        run.font.name = 'Calibri'
        run.bold = negrita
        if color:
            run.font.color.rgb = RGBColor(*color)
        if centrado:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return p
    
    def agregar_tabla(headers, filas, ancho_total=Cm(17)):
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.allow_autofit = False
        table.width = ancho_total
        
        # Encabezados
        hdr_cells = table.rows[0].cells
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
            for paragraph in hdr_cells[i].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.size = Pt(10)
            # Fondo azul
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), '4472C4')
            hdr_cells[i]._tc.get_or_add_tcPr().append(shading_elm)
        
        # Filas
        for fila in filas:
            row_cells = table.add_row().cells
            for i, valor in enumerate(fila):
                row_cells[i].text = str(valor)
                for paragraph in row_cells[i].paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
        
        return table
    
    def salto_pagina():
        doc.add_page_break()
    
    # ============================================================
    # CONTENIDO DEL DOCUMENTO
    # ============================================================
    
    # ---------- PORTADA (Página 1) ----------
    # Espacio
    for _ in range(3):
        parrafo_vacio(20)

    # Título pegado arriba, sin espacio antes, pero con espacio después para separar del subtítulo
    texto_posicionado(doc, "INFORME CONSOLIDADO", posicion='arriba', tamano=30, bold=True, color=(0,0,0))
    # ↑ por defecto space_before=0, space_after=0

    # Subtítulo pegado al título (0 espacio arriba y 0 abajo)
    texto_posicionado(doc, "ACTIVIDADES EFECTUADAS POR", posicion='arriba', tamano=20, color=(100,100,100))

    # NETGROUP pegado al subtítulo
    texto_posicionado(doc, "NETGROUP S.A.", posicion='arriba', tamano=25, bold=True, color=(0,0,0))

    # Espacio superior
    for _ in range(8):
        parrafo_vacio(20)
    
    # Nombre de la empresa (centro)
    nombre_empresa = empresa.get('nombre', 'EMPRESA NO IDENTIFICADA') if empresa else 'EMPRESA NO IDENTIFICADA'
    texto_centrado(nombre_empresa.upper(), tamano=28, bold=True, 
                   color=(0, 0, 0), espacio_despues=40)
    
    # Espacio
    for _ in range(3):
        parrafo_vacio(20)
    
    # ---------- DIRIGIDO A ----------
    dirigido_nombre = empresa.get('dirigido', '') if empresa else ''
    dirigido_cargo = empresa.get('cargo', '') if empresa else ''
    
    # Tabla especial para "Dirigido a"
    table_dir = doc.add_table(rows=0, cols=2)
    table_dir.autofit = False
    table_dir.allow_autofit = False
    table_dir.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    row = table_dir.add_row().cells
    row[0].text = "Dirigido a:"
    row[1].text = f"{dirigido_nombre}\n{dirigido_cargo}"
    
    row[0].width = Cm(4.5)
    row[1].width = Cm(10)
    
    # Formato celda 0
    for paragraph in row[0].paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for run in paragraph.runs:
            run.font.bold = True
            run.font.size = Pt(12)
            run.font.name = 'Calibri'
            run.font.color.rgb = RGBColor(80, 80, 80)
    
    # Formato celda 1 (nombre + cargo)
    for paragraph in row[1].paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in paragraph.runs:
            run.font.size = Pt(12)
            run.font.name = 'Calibri'
            run.font.color.rgb = RGBColor(64, 64, 64)
    
    # Quitar bordes
    for cell in row:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'nil')
            border.set(qn('w:sz'), '0')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'auto')
            tcBorders.append(border)
        tcPr.append(tcBorders)
    
    
    # ---------- INFO ROWS ----------
    ip_servidor = conexion.get('ip_servidor', 'N/A') if conexion else 'N/A'
    fecha_informe = datos.get('fecha_informe', 'N/A')
    
    info_filas = [
        ["Servidor", ip_servidor],
        ["Recopilado por", "Área Bases de Datos"],
        ["Fecha del informe", fecha_informe.title() if isinstance(fecha_informe, str) else fecha_informe],
    ]
    
    tabla_sin_bordes(info_filas, [Cm(4.5), Cm(10)], alineacion_col1=WD_ALIGN_PARAGRAPH.RIGHT)
    
    # Espacio antes del footer
    for _ in range(14):
        parrafo_vacio(0)
    
    # ---------- FOOTER ----------
    footer_p = doc.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_p.add_run(
        "Este documento contiene información confidencial y es de uso "
        "exclusivo del cliente y del personal autorizado de NetGroup S.A."
    )
    footer_run.font.size = Pt(9)
    footer_run.font.name = 'Calibri'
    footer_run.font.color.rgb = RGBColor(128, 128, 128)
    footer_run.italic = True

    # ---------- PÁGINA 2: CONTENIDOS ----------
    salto_pagina()
    
    contenidos = [
        ("1. Métricas Principales", "3"),
        ("2. Tablespaces", "4"),
        ("3. Resumen de Objetos", "5"),
        ("4. Estadísticas de Tablas", "5"),
        ("5. Sistema Operativo", "6"),
        ("6. Filesystems", "6"),
        ("7. Backups Recientes", "7"),
        ("8. Procesos Oracle", "8"),
    ]
    agregar_tabla_contenidos(doc, contenidos)
    
    # ---------- PÁGINA 3: MÉTRICAS ----------
    salto_pagina()

    agregar_titulo("1. Métricas Principales", nivel=1)

    # Espacio
    for _ in range(1):
        parrafo_vacio(20)
    
    metricas = [
        ["Tamaño BD", f"{datos.get('bd_tamano_tb', '0')} TB"],
        ["Objetos Inválidos", str(datos.get('obj_invalidos', 0))],
        ["Uso Filesystem", f"{datos.get('filesystem_pct', '0')}%"],
        ["SGA", f"{datos.get('sga_gb', '0')} GB"],
        ["PGA", f"{datos.get('pga_gb', '0')} GB"],
        ["RAM Usada", f"{datos.get('ram_usada_pct', '0')}%"],
    ]
    agregar_tabla(["Métrica", "Valor"], metricas)

    # Espacio
    for _ in range(2):
        parrafo_vacio(20)

    agregar_titulo("Estado del servidor", nivel=1)

    # Espacio
    for _ in range(1):
        parrafo_vacio(20)

    estado_servidor = [
        ["Uptime", f"{datos.get('uptime', '0')}"],
        ["Load Average", str(datos.get('load_avg', 0))],
    ]
    agregar_tabla(["Métrica", "Valor"],estado_servidor)

    # Espacio
    for _ in range(2):
        parrafo_vacio(20)

    agregar_titulo("Uso de Memoria", nivel=1)

    # Espacio
    for _ in range(1):
        parrafo_vacio(20)

    memoria_ram = [
        ["RAM Usada", f"{datos.get('ram_usada_gb', '0')} GB"],
        ["RAM Disponible", f"{datos.get('ram_disponible_gb', '0')} GB"],
        ["Total RAM",f"{datos.get('ram_total_gb', '0')} GB"],
    ]
    agregar_tabla(["Métrica", "Valor"],memoria_ram)

    # Espacio
    for _ in range(2):
        parrafo_vacio(20)

    agregar_titulo("Procesos Claves de Oracle", nivel=1)

    # Espacio
    for _ in range(1):
        parrafo_vacio(20)

    procesos_ol =  datos.get('procesos_oracle_clave', [])

    procesos_oracle = []
    for proc in procesos_ol:
        procesos_oracle.append([
            proc.get('usuario', 'N/A'),
            proc.get('pid', '0'),
            proc.get('inicio', 'N/A'),
            proc.get('cpu_time', '0:00'),
            proc.get('comando', 'N/A'),
        ])

    agregar_tabla(["Usuario", "PID", "inicio", "CPU Time", "Proceso"],procesos_oracle)
    
    # ---------- PÁGINA 4: TABLESPACES ----------
    salto_pagina()
    agregar_titulo("2. Tablespaces", nivel=1)
    
    ts_headers = ["Nombre", "Asignado (MB)", "Usado (MB)", "% Uso", "Status", "Autoextend"]
    ts_filas = []
    for ts in datos.get('tablespaces', []):
        ts_filas.append([
            ts.get('nombre', 'N/A'),
            ts.get('asignado_mb', 0),
            ts.get('usado_mb', 0),
            f"{ts.get('pct_uso', 0)}%",
            ts.get('status', 'N/A'),
            ts.get('autoextend', 'N/A'),
        ])
    agregar_tabla(ts_headers, ts_filas)
    
    # ---------- PÁGINA 4: OBJETOS Y STATS ----------
    salto_pagina()
    agregar_titulo("3. Resumen de Objetos", nivel=1)
    
    obj = datos.get('resumen_objetos', {})
    obj_filas = [
        ["Tablas", obj.get('tables', 0)],
        ["Índices", obj.get('indexes', 0)],
        ["Paquetes", obj.get('packages', 0)],
        ["Package Bodies", obj.get('package_bodies', 0)],
        ["Triggers", obj.get('triggers', 0)],
        ["Vistas", obj.get('views', 0)],
        ["Secuencias", obj.get('sequences', 0)],
        ["Procedimientos", obj.get('procedures', 0)],
        ["Funciones", obj.get('functions', 0)],
        ["Tipos", obj.get('types', 0)],
        ["Total", obj.get('total', 0)],
    ]
    agregar_tabla(["Tipo de Objeto", "Cantidad"], obj_filas)
    
    agregar_titulo("4. Estadísticas de Tablas", nivel=1)
    stats = datos.get('stats_tablas', {})
    agregar_tabla(
        ["Estado", "Cantidad"],
        [
            ["Actualizadas (≤7 días)", stats.get('actualizadas', 0)],
            ["No actualizadas (>7 días)", stats.get('no_actualizadas', 0)],
            ["Sin estadísticas", stats.get('sin_estadisticas', 0)],
        ]
    )
    
    # ---------- PÁGINA 5: SISTEMA OPERATIVO ----------
    salto_pagina()
    agregar_titulo("5. Sistema Operativo", nivel=1)
    
    so_filas = [
        ["Uptime", datos.get('uptime', 'N/A')],
        ["Load Average", datos.get('load_avg', 'N/A')],
        ["RAM Total", f"{datos.get('ram_total_gb', '0')} GB"],
        ["RAM Usada", f"{datos.get('ram_usada_gb', '0')} GB"],
        ["RAM Disponible", f"{datos.get('ram_disponible_gb', '0')} GB"],
    ]
    agregar_tabla(["Recurso", "Valor"], so_filas)
    
    agregar_titulo("6. Filesystems", nivel=1)
    fs_headers = ["Filesystem", "Tamaño", "Usado", "Disponible", "% Uso", "Montado en"]
    fs_filas = []
    for fs in datos.get('filesystems', []):
        fs_filas.append([
            fs.get('filesystem', 'N/A'),
            fs.get('size', 'N/A'),
            fs.get('used', 'N/A'),
            fs.get('available', 'N/A'),
            fs.get('use_pct', 'N/A'),
            fs.get('mounted_on', 'N/A'),
        ])
    agregar_tabla(fs_headers, fs_filas)
    
    # ---------- BACKUPS (si existen) ----------
    backups = datos.get('backups', [])
    if backups:
        salto_pagina()
        agregar_titulo("7. Backups Recientes", nivel=1)
        bk_headers = ["Archivo", "Tamaño", "Fecha"]
        bk_filas = [[b.get('archivo', ''), b.get('size', ''), b.get('fecha', '')] for b in backups]
        agregar_tabla(bk_headers, bk_filas)
    
    # --- Procesos ---
    procesos = datos.get('procesos_oracle', [])
    if procesos:
        salto_pagina()
        agregar_titulo("8. Procesos Oracle", nivel=1)
        for proc in procesos:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.first_line_indent = Cm(-0.5)
            run = p.add_run(f"• {proc}")
            run.font.size = Pt(10)
            run.font.name = 'Calibri'
    
    # ============================================================
    # GUARDAR (buffer o archivo)
    # ============================================================
    if buffer is not None:
        doc.save(buffer)
        return buffer
    else:
        doc.save(ruta_salida)
        return ruta_salida


