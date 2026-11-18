import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from aplicacion.nucleo.base_datos import obtener_bd
from aplicacion.nucleo.seguridad import obtener_usuario_actual
from aplicacion.nucleo.utilidades import formatear_fecha_es
from aplicacion.modelos.modelos_bd import (
    Usuario, Obra, Coincidencia, EscaneoUrl, Notificacion
)
from aplicacion.esquemas.esquemas_api import (
    EscanearUrlSolicitud,
    ActualizarEstadoCoincidenciaSolicitud
)
from aplicacion.servicios.servicio_imagenes import (
    calcular_sha256_archivo,
    extraer_y_verificar_marca_dct_dwt
)
from aplicacion.servicios.servicio_similitud import (
    descargar_imagen_desde_url_temporal,
    detectar_nombre_plataforma,
    comparar_similitud_obras,
    calcular_hashes_perceptuales,
    obtener_embedding_clip
)
from aplicacion.servicios.servicio_reporte_pdf import generar_pdf_reporte_evidencia

enrutador = APIRouter(prefix="/api/monitoreo", tags=["Monitoreo por URL, Coincidencias y Reportes (US-05, US-11)"])


@enrutador.get("/estado")
def obtener_estado_monitoreo(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    US-05: Calcula en tiempo real desde PostgreSQL las coincidencias por plataforma
    y el historial de URLs temporales escaneadas por el artista.
    """
    obras_ids = [o.id for o in bd.query(Obra).filter(Obra.autor_id == usuario_actual.id).all()]
    coincidencias_usuario = bd.query(Coincidencia).filter(
        Coincidencia.obra_original_id.in_(obras_ids)
    ).all() if obras_ids else []

    escaneos = bd.query(EscaneoUrl).filter(
        EscaneoUrl.usuario_id == usuario_actual.id
    ).order_by(EscaneoUrl.id.desc()).limit(10).all()

    nombres_plataformas = [
        ("Pinterest", 48),
        ("Instagram", 65),
        ("Behance", 78),
        ("ArtStation", 92),
        ("X / Twitter", 44),
        ("Tumblr", 56),
        ("Reddit", 74),
        ("Google Images", 90),
        ("URL Web Externa", 100),
    ]

    historial_dinamico = []
    for nombre_plat, progreso_base in nombres_plataformas:
        cant = sum(1 for c in coincidencias_usuario if c.plataforma.lower() == nombre_plat.lower())
        if nombre_plat == "URL Web Externa" and cant == 0 and not escaneos:
            continue
        historial_dinamico.append({
            "nombre": nombre_plat,
            "progreso": progreso_base,
            "estado": f"{cant} coincidencia{'s' if cant != 1 else ''}" if cant > 0 else "Sin cambios",
            "alerta": cant > 0
        })

    return {
        "plataformas_monitoreadas": len(historial_dinamico),
        "ultima_revision": "en tiempo real",
        "estado_global": "Activo" if obras_ids else "Sin obras en vigilancia",
        "historial_plataformas": historial_dinamico,
        "escaneos_url_recientes": [
            {
                "id": e.id,
                "url_ingresada": e.url_ingresada,
                "plataforma_detectada": e.plataforma_detectada,
                "coincidencias_halladas": e.coincidencias_halladas,
                "mayor_similitud": e.mayor_similitud,
                "estado_escaneo": e.estado_escaneo,
                "fecha": e.fecha_escaneo.strftime("%d/%m/%Y %H:%M")
            }
            for e in escaneos
        ]
    }


@enrutador.post("/escanear-url")
def analizar_url_temporal(
    datos: EscanearUrlSolicitud,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    US-05: Recibe una URL temporal dada por el usuario, descarga la imagen de esa URL
    y la compara matemáticamente (imageHash + CLIP + DCT/DWT) contra las obras del artista.
    """
    try:
        ruta_descargada = descargar_imagen_desde_url_temporal(datos.url_temporal.strip())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo obtener una imagen válida desde la URL proporcionada: {e}"
        )

    consulta_obras = bd.query(Obra).filter(Obra.autor_id == usuario_actual.id)
    if datos.obra_id:
        consulta_obras = consulta_obras.filter(Obra.id == datos.obra_id)
    obras_a_comparar = consulta_obras.all()

    if not obras_a_comparar:
        raise HTTPException(
            status_code=400,
            detail="Primero debes tener al menos una obra registrada en AegisArt para buscar similitudes."
        )

    plataforma = detectar_nombre_plataforma(datos.url_temporal)
    phash_cand, _ = calcular_hashes_perceptuales(ruta_descargada)
    vec_clip_cand = obtener_embedding_clip(ruta_descargada)
    marca_cand, _ = extraer_y_verificar_marca_dct_dwt(ruta_descargada)
    hash_cand = calcular_sha256_archivo(ruta_descargada)[:18]

    mejor_resultado = None
    mejor_obra = None
    mejor_criterio = (-1.0, -1.0)

    for obra in obras_a_comparar:
        if not obra.huella:
            continue
        comp = comparar_similitud_obras(
            phash_original=obra.huella.hash_phash,
            embedding_original_json=obra.huella.embedding_clip_json,
            ruta_imagen_candidata=ruta_descargada,
            phash_candidata=phash_cand,
            embedding_candidata=vec_clip_cand,
            marca_detectada_candidata=marca_cand,
            hash_copia_candidata=hash_cand,
        )
        criterio = (
            comp["porcentaje_similitud"],
            round(comp["similitud_visual_phash"] * 0.55 + comp["similitud_semantica_clip"] * 0.45, 2),
        )
        if mejor_resultado is None or criterio > mejor_criterio:
            mejor_criterio = criterio
            mejor_resultado = comp
            mejor_obra = obra

    if not mejor_resultado or not mejor_obra:
        raise HTTPException(status_code=400, detail="No se pudo completar el análisis de similitud.")

    porcentaje = mejor_resultado["porcentaje_similitud"]
    coincidencia_creada = None

    # Si supera el 65% de similitud, se registra como una nueva coincidencia detectada
    if porcentaje >= 65.0:
        siguiente_num = (bd.query(func.max(Coincidencia.id)).scalar() or 0) + 3
        codigo_caso = f"AEG-2026-{siguiente_num:03d}"
        while bd.query(Coincidencia).filter(Coincidencia.codigo_caso == codigo_caso).first():
            siguiente_num += 1
            codigo_caso = f"AEG-2026-{siguiente_num:03d}"

        coincidencia_creada = Coincidencia(
            codigo_caso=codigo_caso,
            obra_original_id=mejor_obra.id,
            plataforma=plataforma,
            url_detectada=datos.url_temporal.strip(),
            ruta_imagen_copia=ruta_descargada,
            porcentaje_similitud=porcentaje,
            similitud_visual_phash=mejor_resultado["similitud_visual_phash"],
            similitud_semantica_clip=mejor_resultado["similitud_semantica_clip"],
            diferencias_detectadas=mejor_resultado["diferencias_detectadas"],
            marca_invisible_identificada=mejor_resultado["marca_invisible_identificada"],
            hash_copia_detectada=mejor_resultado["hash_copia_detectada"],
            estado_artista="Pendiente",
            enviado_a_moderacion=porcentaje >= 90.0,
            motivo_reporte="Coincidencia automática >= 90% por URL" if porcentaje >= 90.0 else None,
            estado_moderador="En revisión" if porcentaje >= 90.0 else None
        )
        mejor_obra.estado = "Coincidencia encontrada"
        bd.add(coincidencia_creada)
        bd.flush()

        # Notificar al artista dueño de la obra
        bd.add(Notificacion(
            usuario_destino_id=usuario_actual.id,
            rol_destino="artista",
            titulo=f"Nueva coincidencia ({porcentaje}%)",
            mensaje=f"Se detectó una copia potencial de '{mejor_obra.titulo}' en {plataforma}.",
            tipo="coincidencia",
            referencia_codigo=codigo_caso
        ))

        if porcentaje >= 90.0:
            for mod in bd.query(Usuario).filter(Usuario.rol.in_(["moderador", "dueno"])).all():
                bd.add(Notificacion(
                    usuario_destino_id=mod.id,
                    rol_destino="moderador",
                    titulo=f"Coincidencia crítica ({porcentaje}%): {codigo_caso}",
                    mensaje=f"Similitud detectada en {plataforma} sobre '{mejor_obra.titulo}'.",
                    tipo="coincidencia",
                    referencia_codigo=codigo_caso
                ))

    nuevo_escaneo = EscaneoUrl(
        usuario_id=usuario_actual.id,
        obra_objetivo_id=mejor_obra.id,
        url_ingresada=datos.url_temporal.strip(),
        plataforma_detectada=plataforma,
        coincidencias_halladas=1 if coincidencia_creada else 0,
        mayor_similitud=porcentaje,
        estado_escaneo="1 coincidencia detectada" if coincidencia_creada else "Sin coincidencias"
    )
    bd.add(nuevo_escaneo)
    bd.commit()

    return {
        "mensaje": (
            f"Se detectó una similitud del {porcentaje}% con tu obra '{mejor_obra.titulo}'."
            if coincidencia_creada
            else f"Análisis finalizado ({porcentaje}% de similitud). No se encontraron copias significativas."
        ),
        "coincidencia_detectada": coincidencia_creada is not None,
        "porcentaje_similitud": porcentaje,
        "similitud_visual_phash": mejor_resultado["similitud_visual_phash"],
        "similitud_semantica_clip": mejor_resultado["similitud_semantica_clip"],
        "marca_invisible_identificada": mejor_resultado["marca_invisible_identificada"],
        "obra_comparada": mejor_obra.titulo,
        "coincidencia_id": coincidencia_creada.id if coincidencia_creada else None,
        "codigo_caso": coincidencia_creada.codigo_caso if coincidencia_creada else None
    }


@enrutador.get("/coincidencias")
def listar_coincidencias(
    filtro: str = "Todas",
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    US-05: Lista las coincidencias detectadas con los filtros de Figma:
    'Todas', 'Similitud > 90%', 'Últimas 24 horas'.
    """
    obras_ids = [o.id for o in bd.query(Obra).filter(Obra.autor_id == usuario_actual.id).all()]
    if not obras_ids:
        return []

    consulta = bd.query(Coincidencia).filter(Coincidencia.obra_original_id.in_(obras_ids))
    if filtro == "Similitud > 90%":
        consulta = consulta.filter(Coincidencia.porcentaje_similitud >= 90.0)
    elif filtro == "Últimas 24 horas":
        hace_24h = datetime.utcnow() - timedelta(hours=24)
        consulta = consulta.filter(Coincidencia.fecha_deteccion >= hace_24h)

    lista = consulta.order_by(Coincidencia.porcentaje_similitud.desc()).all()

    salida = []
    for c in lista:
        obra_orig = c.obra_original
        archivo_orig = os.path.basename(obra_orig.ruta_protegida or obra_orig.ruta_original)
        url_img_orig = f"http://localhost:8000/archivos/protegidas/{archivo_orig}"

        if c.ruta_imagen_copia and "analizadas_url" in c.ruta_imagen_copia:
            url_img_copia = f"http://localhost:8000/archivos/analizadas_url/{os.path.basename(c.ruta_imagen_copia)}"
        else:
            url_img_copia = url_img_orig

        salida.append({
            "id": c.id,
            "codigo_caso": c.codigo_caso,
            "obra_id": obra_orig.id,
            "titulo_obra": obra_orig.titulo,
            "plataforma": c.plataforma,
            "url_detectada": c.url_detectada,
            "porcentaje_similitud": c.porcentaje_similitud,
            "diferencias_detectadas": c.diferencias_detectadas,
            "marca_invisible_identificada": c.marca_invisible_identificada,
            "estado_artista": c.estado_artista,
            "url_imagen_original": url_img_orig,
            "url_imagen_copia": url_img_copia,
            "fecha_deteccion": formatear_fecha_es(c.fecha_deteccion, "corto_coma")
        })
    return salida


@enrutador.get("/coincidencias/{coincidencia_id}")
def obtener_detalle_coincidencia(coincidencia_id: int, bd: Session = Depends(obtener_bd)):
    """
    US-05 y US-11: Devuelve todos los datos para las pantallas 'Revisión de coincidencia'
    y 'Reporte de evidencia · AEG-2026-003'.
    """
    c = bd.query(Coincidencia).filter(Coincidencia.id == coincidencia_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coincidencia no encontrada.")

    obra = c.obra_original
    archivo_orig = os.path.basename(obra.ruta_protegida or obra.ruta_original)
    url_img_orig = f"http://localhost:8000/archivos/protegidas/{archivo_orig}"

    if c.ruta_imagen_copia and "analizadas_url" in c.ruta_imagen_copia:
        url_img_copia = f"http://localhost:8000/archivos/analizadas_url/{os.path.basename(c.ruta_imagen_copia)}"
    else:
        url_img_copia = url_img_orig

    return {
        "id": c.id,
        "codigo_caso": c.codigo_caso,
        "obra_id": obra.id,
        "titulo_obra": obra.titulo,
        "autor": obra.autor.nombre_apellido if obra.autor else "Nayeli Castillo",
        "plataforma": c.plataforma,
        "url_detectada": c.url_detectada,
        "porcentaje_similitud": c.porcentaje_similitud,
        "similitud_visual_phash": c.similitud_visual_phash,
        "similitud_semantica_clip": c.similitud_semantica_clip,
        "diferencias_detectadas": c.diferencias_detectadas,
        "marca_invisible_identificada": c.marca_invisible_identificada,
        "hash_original": obra.huella.hash_sha256 if obra.huella else "0x8f72...31d5",
        "hash_original_corto": (obra.huella.hash_sha256[:10] + "..." + obra.huella.hash_sha256[-4:]) if obra.huella else "0x8f72...31d5",
        "hash_copia_corto": c.hash_copia_detectada[:10] + "..." + c.hash_copia_detectada[-4:],
        "transaccion_blockchain": obra.registro_blockchain.hash_transaccion if obra.registro_blockchain else "0x3ac9...e720",
        "codigo_certificado": obra.registro_blockchain.codigo_certificado if obra.registro_blockchain else "AEG-2026-0024",
        "estado_artista": c.estado_artista,
        "estado_moderador": c.estado_moderador,
        "comentarios_moderador": c.comentarios_moderador,
        "url_imagen_original": url_img_orig,
        "url_imagen_copia": url_img_copia,
        "fecha_registro_obra": formatear_fecha_es(obra.fecha_registro, "dia_mes"),
        "fecha_deteccion": formatear_fecha_es(c.fecha_deteccion, "dia_mes")
    }


@enrutador.put("/coincidencias/{coincidencia_id}/estado")
def actualizar_estado_coincidencia(
    coincidencia_id: int,
    datos: ActualizarEstadoCoincidenciaSolicitud,
    bd: Session = Depends(obtener_bd)
):
    """
    US-05: Botones 'Confirmar plagio', 'Descartar coincidencia' e 'Iniciar reclamo ->'.
    """
    c = bd.query(Coincidencia).filter(Coincidencia.id == coincidencia_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coincidencia no encontrada.")

    if datos.estado_artista == "Reclamo":
        c.estado_artista = "Confirmado"
        c.enviado_a_moderacion = True
        c.estado_moderador = "En revisión"
        c.motivo_reporte = c.motivo_reporte or "Uso sin autorización"
        for mod in bd.query(Usuario).filter(Usuario.rol.in_(["moderador", "dueno"])).all():
            bd.add(Notificacion(
                usuario_destino_id=mod.id,
                rol_destino="moderador",
                titulo=f"Apelación enviada a revisión: {c.codigo_caso}",
                mensaje=f"Reclamo formal sobre '{c.obra_original.titulo}' ({c.porcentaje_similitud}% similitud).",
                tipo="coincidencia",
                referencia_codigo=c.codigo_caso
            ))
    else:
        c.estado_artista = datos.estado_artista

    bd.commit()
    return {"mensaje": f"Estado de la coincidencia actualizado a '{c.estado_artista}'."}


@enrutador.get("/coincidencias/{coincidencia_id}/descargar-reporte-pdf")
def descargar_reporte_autoria_pdf(coincidencia_id: int, bd: Session = Depends(obtener_bd)):
    """
    US-11: Descarga el reporte de autoría legal en formato PDF con toda la evidencia técnica.
    """
    c = bd.query(Coincidencia).filter(Coincidencia.id == coincidencia_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coincidencia no encontrada.")

    obra = c.obra_original
    datos_pdf = {
        "codigo_caso": c.codigo_caso,
        "titulo_obra": obra.titulo,
        "autor": obra.autor.nombre_apellido if obra.autor else "Nayeli Castillo",
        "codigo_certificado": obra.registro_blockchain.codigo_certificado if obra.registro_blockchain else "AEG-2026-0024",
        "fecha_registro": formatear_fecha_es(obra.fecha_registro, "largo"),
        "hash_original": obra.huella.hash_sha256 if obra.huella else "0x8f72a9c4e6b031d5",
        "tx_blockchain": obra.registro_blockchain.hash_transaccion if obra.registro_blockchain else "0x3ac9...e720",
        "direccion_contrato": obra.registro_blockchain.direccion_contrato if obra.registro_blockchain else "",
        "plataforma": c.plataforma,
        "url_detectada": c.url_detectada,
        "porcentaje_similitud": c.porcentaje_similitud,
        "marca_identificada": c.marca_invisible_identificada,
        "hash_copia": c.hash_copia_detectada,
        "diferencias": c.diferencias_detectadas
    }
    pdf_bytes = generar_pdf_reporte_evidencia(datos_pdf)
    nombre_descarga = f"Reporte_Evidencia_{c.codigo_caso}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre_descarga}"'}
    )