# reportes/services.py
import json
import io
import paramiko
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def obtener_metricas_oracle(host, user, password, port=22, script_remoto="/u01/app/oracle/scripts/extraer_metricas_json.sh"):
    """Conecta vía SSH usando los parámetros dinámicos de la BD."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Conexión SSH con los datos dinámicos recibidos
    ssh.connect(
        hostname=host, 
        username=user, 
        password=password, 
        port=port, 
        timeout=10
    )

    # Invocamos el script forzando la carga de variables de entorno con un Shell Login
    stdin, stdout, stderr = ssh.exec_command(f"bash -l {script_remoto}")
    
    salida_texto = stdout.read().decode('utf-8').strip()
    salida_error = stderr.read().decode('utf-8').strip()
    ssh.close()

    # Si hay errores en stderr, lanzamos la excepción con ese mensaje
    if salida_error and not salida_texto:
        raise Exception(f"Error en script SSH: {salida_error}")
        
    try:
        return json.loads(salida_texto)
    except json.JSONDecodeError:
        # Esto te mostrará en pantalla qué texto extraño devolvió el servidor en vez de JSON
        raise Exception(f"Salida no válida recibida del servidor:\n'{salida_texto}'")
    

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def construir_documento_docx(datos):
    """Construye el documento Word en memoria y retorna un BytesIO buffer."""
    doc = Document()
    
    # Márgenes
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Estilo Normal
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(10)
    style.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Header
    p_hdr = doc.add_paragraph()
    r_sub = p_hdr.add_run("INFORME MENSUAL · BASE DE DATOS ORACLE\n")
    r_sub.font.size = Pt(9)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(0x77, 0x77, 0x77)
    
    r_title = p_hdr.add_run(f"{datos['fecha_informe'].capitalize()}")
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x18, 0x5F, 0xA5)

    # 1. Resumen Ejecutivo
    p_sec = doc.add_paragraph()
    p_sec.paragraph_format.space_before = Pt(14)
    r_sec = p_sec.add_run("1. RESUMEN EJECUTIVO")
    r_sec.font.bold = True
    r_sec.font.color.rgb = RGBColor(0x18, 0x5F, 0xA5)

    tbl_kpi = doc.add_table(rows=2, cols=4)
    tbl_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    kpis = [
        ("BD tamaño", f"{datos['bd_tamano_tb']} TB"),
        ("Filesystem", f"{datos['filesystem_pct']}%"),
        ("Backups", "30/30"),
        ("Obj. inválidos", str(datos['obj_invalidos']))
    ]
    for i, (label, val) in enumerate(kpis):
        cell_lbl, cell_val = tbl_kpi.cell(0, i), tbl_kpi.cell(1, i)
        set_cell_background(cell_lbl, "F0F4F8")
        set_cell_background(cell_val, "F0F4F8")
        
        p0 = cell_lbl.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.add_run(label).font.size = Pt(9)
        
        p1 = cell_val.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p1.add_run(val)
        r.font.size = Pt(13)
        r.font.bold = True

    # 2. Tablespaces
    p_sec2 = doc.add_paragraph()
    p_sec2.paragraph_format.space_before = Pt(14)
    r_sec2 = p_sec2.add_run("2. USO DE TABLESPACES")
    r_sec2.font.bold = True
    r_sec2.font.color.rgb = RGBColor(0x18, 0x5F, 0xA5)

    tbl_ts = doc.add_table(rows=1, cols=4)
    tbl_ts.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Tablespace", "Asignado (MB)", "Usado (MB)", "% Uso"]
    for i, h in enumerate(headers):
        cell = tbl_ts.rows[0].cells[i]
        set_cell_background(cell, "185FA5")
        p = cell.paragraphs[0]
        if i > 0: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    ts_sorted = sorted(datos['tablespaces'], key=lambda x: x['pct_uso'], reverse=True)
    for item in ts_sorted[:8]:
        row = tbl_ts.add_row().cells
        row[0].paragraphs[0].add_run(item['nombre'])

        p1 = row[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.add_run(f"{item['file_name']:,}")

        p2 = row[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p2.add_run(f"{item['status']:,}")

        p3 = row[3].paragraphs[0]
        p3.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p3.add_run(f"{item['autoextend']:,}")
        
        p4 = row[4].paragraphs[0]
        p4.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p4.add_run(f"{item['asignado_mb']:,}")
        
        p5 = row[5].paragraphs[0]
        p5.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p5.add_run(f"{item['usado_mb']:,}")
        
        p6 = row[6].paragraphs[0]
        p6.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_pct = p6.add_run(f"{item['pct_uso']}%")
        r_pct.font.bold = True
        
        if item['pct_uso'] >= 90:
            r_pct.font.color.rgb = RGBColor(0xD8, 0x30, 0x30)
            set_cell_background(row[3], "FDE8E8")
        elif item['pct_uso'] >= 70:
            r_pct.font.color.rgb = RGBColor(0xD8, 0x8A, 0x30)
            set_cell_background(row[3], "FFF7E6")

    # Guardar en buffer en memoria
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer