import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def generar_pdf_reporte_evidencia(datos_reporte: dict) -> bytes:
    """
    Genera en memoria un archivo PDF pericial con los datos del Certificado y del
    Reporte de Evidencia (US-03 y US-11).
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    # Encabezado morado identidad AegisArt
    c.setFillColor(colors.HexColor("#2D1B4E"))
    c.rect(0, alto - 100, ancho, 100, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, alto - 50, "AegisArt · Reporte Pericial de Autoría y Evidencia")
    c.setFont("Helvetica", 11)
    c.drawString(40, alto - 75, f"Código de Caso / Reporte: {datos_reporte.get('codigo_caso', 'AEG-2026-003')}")

    # Bloque 1: Datos de la Obra Original y Certificado
    y = alto - 140
    c.setFillColor(colors.HexColor("#1F1635"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "1. Certificado de Autoría y Prueba de Génesis (Blockchain)")

    y -= 25
    c.setFont("Helvetica", 11)
    lineas_obra = [
        f"Título de la Obra Original: {datos_reporte.get('titulo_obra', 'Ecos de otro mundo')}",
        f"Autor(a) Registrado(a): {datos_reporte.get('autor', 'Nayeli Castillo')}",
        f"ID del Certificado Digital: {datos_reporte.get('codigo_certificado', 'AEG-2026-0024')}",
        f"Fecha de Registro: {datos_reporte.get('fecha_registro', '18 junio 2026')}",
        f"Huella Criptográfica Original (SHA-256): {datos_reporte.get('hash_original', '')[:48]}...",
        f"Transacción Blockchain (Hardhat EVM): {datos_reporte.get('tx_blockchain', '')[:48]}...",
        f"Dirección del Smart Contract: {datos_reporte.get('direccion_contrato', '0x5FbDB2315678afecb367f032d93F642f64180aa3')}"
    ]
    for linea in lineas_obra:
        c.drawString(50, y, linea)
        y -= 20

    # Bloque 2: Evidencia Técnica de la Coincidencia Detectada
    y -= 15
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "2. Evidencia Técnica de Similitud y Esteganografía (DCT/DWT)")

    y -= 25
    c.setFont("Helvetica", 11)
    marca_txt = "SÍ (Marca invisible identificada)" if datos_reporte.get("marca_identificada", True) else "No detectada"
    lineas_evidencia = [
        f"Plataforma / Origen Detectado: {datos_reporte.get('plataforma', 'Instagram')}",
        f"URL Analizada: {datos_reporte.get('url_detectada', 'https://instagram.com/p/repost_no_autorizado_1')}",
        f"Nivel de Similitud Visual y Semántica (pHash + CLIP): {datos_reporte.get('porcentaje_similitud', 98.2)}%",
        f"Estado de Marca Invisible (DCT/DWT): {marca_txt}",
        f"Hash de la Copia Detectada: {datos_reporte.get('hash_copia', '0x7e45...12c4')}",
        f"Diferencias Visuales Detectadas: {datos_reporte.get('diferencias', 'Recorte de bordes · Ajuste de color')}"
    ]
    for linea in lineas_evidencia:
        c.drawString(50, y, linea)
        y -= 20

    # Bloque 3: Cronología del Caso
    y -= 15
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "3. La Historia de tu Obra (Trazabilidad Cronológica)")

    y -= 25
    c.setFont("Helvetica", 11)
    pasos = [
        "• Paso 1: Registro de autoría y blindaje preventivo en AegisArt.",
        "• Paso 2: Coincidencia detectada mediante monitoreo de URL.",
        f"• Paso 3: Similitud calculada del {datos_reporte.get('porcentaje_similitud', 98.2)}% verificada con imageHash y CLIP.",
        "• Paso 4: Evidencia técnica generada para reclamo DMCA / Take-Down o disputa legal."
    ]
    for paso in pasos:
        c.drawString(50, y, paso)
        y -= 20

    # Pie de página
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawString(
        40, 50,
        "Documento generado automáticamente por AegisArt (2026). Respaldo técnico auditable para reclamos de autoría."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()