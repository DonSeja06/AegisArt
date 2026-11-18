import os
import json
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import Session
from aplicacion.nucleo.base_datos import obtener_bd
from aplicacion.nucleo.seguridad import obtener_usuario_actual
from aplicacion.nucleo.utilidades import formatear_fecha_es
from aplicacion.modelos.modelos_bd import (
    Usuario, Obra, HuellaObra, RegistroBlockchain, Coincidencia, Notificacion
)
from aplicacion.servicios.servicio_imagenes import (
    validar_archivo_imagen,
    procesar_y_blindar_obra,
    extraer_y_verificar_marca_dct_dwt
)
from aplicacion.servicios.servicio_similitud import (
    calcular_hashes_perceptuales,
    obtener_embedding_clip,
    comparar_similitud_obras
)
from aplicacion.servicios.servicio_blockchain import (
    registrar_obra_en_blockchain,
    consultar_obra_en_blockchain
)
from aplicacion.servicios.servicio_nube_r2 import subir_obra_a_cloudflare_r2
from aplicacion.servicios.servicio_ia_apf3 import predecir_obra_sospechosa_ml

enrutador = APIRouter(prefix="/api/obras", tags=["Gestión y Protección de Obras (US-02, US-03, US-04, US-08, US-09)"])


@enrutador.get("/resumen-inicio")
def obtener_resumen_inicio(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    Datos 100% dinámicos desde PostgreSQL para la pantalla 'Inicio'.
    """
    obras_usuario = bd.query(Obra).filter(Obra.autor_id == usuario_actual.id).order_by(Obra.fecha_registro.desc()).all()
    ids_obras = [o.id for o in obras_usuario]

    total_protegidas = len(obras_usuario)
    total_monitoreando = sum(1 for o in obras_usuario if o.estado in ("Monitoreando", "Protegida", "Coincidencia encontrada"))
    total_certificados = bd.query(RegistroBlockchain).filter(
        RegistroBlockchain.obra_id.in_(ids_obras)
    ).count() if ids_obras else 0

    coincidencias = bd.query(Coincidencia).filter(
        Coincidencia.obra_original_id.in_(ids_obras)
    ).order_by(Coincidencia.fecha_deteccion.desc()).all() if ids_obras else []

    notificaciones = bd.query(Notificacion).filter(
        Notificacion.usuario_destino_id == usuario_actual.id
    ).order_by(Notificacion.fecha_creacion.desc()).limit(5).all()

    # Construir actividad reciente real a partir de las obras, certificados y coincidencias del usuario
    actividad_dinamica = []
    if coincidencias:
        actividad_dinamica.append({
            "etiqueta": f"Coincidencia detectada ({coincidencias[0].porcentaje_similitud}%)",
            "tiempo": coincidencias[0].fecha_deteccion.strftime("%d/%m %H:%M"),
            "tipo": "alerta"
        })
    if obras_usuario:
        actividad_dinamica.append({
            "etiqueta": f"Certificado disponible ({obras_usuario[0].titulo})",
            "tiempo": obras_usuario[0].fecha_registro.strftime("%d/%m %H:%M"),
            "tipo": "exito"
        })
        actividad_dinamica.append({
            "etiqueta": f"Monitoreo activo ({total_monitoreando} obras)",
            "tiempo": "Actualizado",
            "tipo": "info"
        })
    else:
        actividad_dinamica.append({
            "etiqueta": "Cuenta creada sin obras registradas aún",
            "tiempo": "Hoy",
            "tipo": "info"
        })

    return {
        "nombre_saludo": usuario_actual.nombre_apellido.split()[0],
        "metricas": {
            "obras_protegidas": total_protegidas,
            "coincidencias": len(coincidencias),
            "monitoreando": total_monitoreando,
            "certificados": total_certificados
        },
        "vigilancia_semanas": [
            max(0, len(coincidencias) - 2),
            max(0, len(coincidencias) - 1),
            len(coincidencias),
            total_protegidas,
            total_certificados,
            len(coincidencias) + total_protegidas
        ],
        "actividad_reciente": actividad_dinamica,
        "notificaciones": [
            {
                "id": n.id,
                "titulo": n.titulo,
                "mensaje": n.mensaje,
                "tipo": n.tipo,
                "referencia_codigo": n.referencia_codigo
            }
            for n in notificaciones
        ]
    }


@enrutador.get("/catalogo-inspiracion")
def listar_catalogo_para_inspiracion(bd: Session = Depends(obtener_bd)):
    """
    US-08: Devuelve la lista de obras previamente registradas en la plataforma para que
    el artista pueda declarar que su nueva obra fue inspirada en una existente.
    """
    obras = bd.query(Obra).order_by(Obra.id.asc()).all()
    return [
        {
            "id": o.id,
            "codigo_obra": o.codigo_obra,
            "titulo": o.titulo,
            "autor": o.autor.nombre_apellido if o.autor else "Artista AegisArt"
        }
        for o in obras
    ]


@enrutador.get("")
def listar_mis_obras(
    buscar: Optional[str] = None,
    filtro_estado: Optional[str] = "Todas",
    solo_usuario: bool = True,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    US-04: Visualizar todas las obras registradas en 'Mis obras' con búsqueda y filtros
    (Todas, Protegidas, Monitoreando, Coincidencia encontrada).
    """
    consulta = bd.query(Obra)
    if solo_usuario:
        consulta = consulta.filter(Obra.autor_id == usuario_actual.id)

    if buscar and buscar.strip():
        consulta = consulta.filter(Obra.titulo.ilike(f"%{buscar.strip()}%"))

    if filtro_estado and filtro_estado not in ("Todas", "Todos"):
        if filtro_estado == "Protegidas":
            consulta = consulta.filter(Obra.estado == "Protegida")
        elif filtro_estado == "Monitoreando":
            consulta = consulta.filter(Obra.estado == "Monitoreando")
        elif filtro_estado == "Coincidencia encontrada":
            consulta = consulta.filter(Obra.estado == "Coincidencia encontrada")

    obras = consulta.order_by(Obra.id.desc()).all()

    resultado = []
    for o in obras:
        resultado.append({
            "id": o.id,
            "codigo_obra": o.codigo_obra,
            "titulo": o.titulo,
            "descripcion": o.descripcion,
            "formato": o.formato,
            "tamano_mb": o.tamano_mb,
            "estado": o.estado,
            "nivel_proteccion": o.nivel_proteccion,
            "proteccion_ia_activa": o.proteccion_ia_activa,
            "marca_invisible_activa": o.marca_invisible_activa,
            "fecha_registro": formatear_fecha_es(o.fecha_registro, "corto_coma"),
            "url_imagen": f"http://localhost:8000/archivos/protegidas/{os.path.basename(o.ruta_protegida or o.ruta_original)}",
            "hash_sha256": o.huella.hash_sha256 if o.huella else "",
            "codigo_certificado": o.registro_blockchain.codigo_certificado if o.registro_blockchain else "",
            "obra_inspirada_id": o.obra_inspirada_id,
            "obra_inspirada_titulo": o.obra_inspirada_en.titulo if o.obra_inspirada_en else None,
            "es_sospechosa": o.es_sospechosa,
            "motivo_sospecha": o.motivo_sospecha,
            "estado_moderacion": o.estado_moderacion
        })
    return resultado


@enrutador.post("/proteger-y-registrar")
async def proteger_y_registrar_nueva_obra(
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(""),
    nivel_proteccion: str = Form("Equilibrada"),
    obra_inspirada_id: Optional[int] = Form(None),
    archivo: UploadFile = File(...),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    Ejecuta en cadena:
    - US-02: Validación de imagen (PNG, JPG, WEBP <= 20 MB) y título obligatorio (<= 120 caracteres).
    - US-03: Perturbación anti-IA (Glaze), marca invisible (DCT/DWT), huella SHA-256 y registro en Smart Contract.
    - US-08: Vinculación opcional con una obra previa de referencia ("Obra inspirada en...").
    - US-09: Evaluación automática de obra sospechosa y envío de notificación a moderadores activos.
    """
    titulo_limpio = titulo.strip()
    if not titulo_limpio:
        raise HTTPException(status_code=400, detail="El título de la obra es obligatorio.")
    if len(titulo_limpio) > 120:
        raise HTTPException(status_code=400, detail="El título no puede superar los 120 caracteres.")

    contenido_bytes = await archivo.read()
    es_valido, mensaje_val, formato_norm, tamano_mb = validar_archivo_imagen(
        archivo.filename or "", len(contenido_bytes)
    )
    if not es_valido:
        raise HTTPException(status_code=400, detail=mensaje_val)

    # Verificar huella SHA-256 exacta antes de escribir archivos o subir a R2
    hash_sha256_previo = "0x" + hashlib.sha256(contenido_bytes).hexdigest()
    if bd.query(HuellaObra).filter(HuellaObra.hash_sha256 == hash_sha256_previo).first():
        raise HTTPException(
            status_code=400,
            detail="Esta obra exacta (misma huella SHA-256) ya se encuentra registrada en AegisArt."
        )

    # Generar correlativo único de obra y certificado
    max_id = bd.query(func.max(Obra.id)).scalar() or 0
    siguiente_num = max_id + 1
    codigo_obra = f"OBRA-{siguiente_num:03d}"
    codigo_certificado = f"AEG-2026-{siguiente_num + 23:04d}"

    nombre_archivo_limpio = os.path.basename(archivo.filename or f"obra.{formato_norm.lower()}")
    nombre_seguro = f"{codigo_obra.lower()}_{nombre_archivo_limpio}"
    ruta_original = os.path.join("archivos_subidos", "originales", nombre_seguro)
    ruta_protegida = os.path.join("archivos_subidos", "protegidas", nombre_seguro)

    os.makedirs(os.path.dirname(ruta_original), exist_ok=True)
    with open(ruta_original, "wb") as f:
        f.write(contenido_bytes)

    # Paso 1 y 2: Blindar con Glaze + Marca Invisible DCT/DWT + Calcular SHA-256
    try:
        datos_blindaje = procesar_y_blindar_obra(
            ruta_original=ruta_original,
            ruta_protegida=ruta_protegida,
            codigo_obra=codigo_obra,
            nivel_proteccion=nivel_proteccion
        )
    except ValueError as err:
        if os.path.exists(ruta_original):
            os.remove(ruta_original)
        raise HTTPException(status_code=400, detail=f"Archivo de imagen corrupto o ilegible: {err}")

    # Subir imagen protegida al bucket de Cloudflare R2
    info_r2 = subir_obra_a_cloudflare_r2(ruta_protegida, nombre_seguro)

    # Calcular imageHash (pHash/dHash), vector semántico CLIP (512-d) y detectar si ya trae marca DCT/DWT previa una sola vez
    phash, dhash = calcular_hashes_perceptuales(ruta_original)
    vector_clip = obtener_embedding_clip(ruta_original)
    marca_ajena_detectada, _ = extraer_y_verificar_marca_dct_dwt(ruta_original)
    hash_copia_corto = datos_blindaje["hash_sha256"][:18]

    # Calcular la mejor coincidencia perceptual/semántica contra el catálogo actual sin recálculo O(N)
    mayor_similitud_catalogo = 0.0
    mejor_similitud_phash = 0.0
    mejor_similitud_clip = 0.0
    mejor_criterio = (-1.0, -1.0)
    for h_existente in bd.query(HuellaObra).all():
        comp = comparar_similitud_obras(
            phash_original=h_existente.hash_phash,
            embedding_original_json=h_existente.embedding_clip_json,
            ruta_imagen_candidata=ruta_original,
            phash_candidata=phash,
            embedding_candidata=vector_clip,
            marca_detectada_candidata=marca_ajena_detectada,
            hash_copia_candidata=hash_copia_corto,
        )
        criterio = (
            comp["porcentaje_similitud"],
            round(comp["similitud_visual_phash"] * 0.55 + comp["similitud_semantica_clip"] * 0.45, 2),
        )
        if criterio > mejor_criterio:
            mejor_criterio = criterio
            mayor_similitud_catalogo = comp["porcentaje_similitud"]
            mejor_similitud_phash = comp["similitud_visual_phash"]
            mejor_similitud_clip = comp["similitud_semantica_clip"]

    # US-09 + APF3 Ruta A: Clasificar con el modelo Gradient Boosting entrenado (scikit-learn)
    resultado_ml = predecir_obra_sospechosa_ml(
        ruta_imagen=ruta_original,
        titulo=titulo_limpio,
        similitud_maxima=mayor_similitud_catalogo,
        declarada_inspirada=bool(obra_inspirada_id and obra_inspirada_id > 0),
        similitud_phash=mejor_similitud_phash,
        similitud_clip=mejor_similitud_clip,
        marca_ajena_detectada=marca_ajena_detectada,
    )
    es_sospechosa = resultado_ml["es_sospechosa"]
    motivo_sospecha = resultado_ml["motivo_sospecha"]
    
    # Paso 5: Registrar en PostgreSQL
    nueva_obra = Obra(
        codigo_obra=codigo_obra,
        titulo=titulo_limpio,
        descripcion=descripcion or "",
        nombre_archivo=nombre_archivo_limpio,
        formato=formato_norm,
        tamano_mb=tamano_mb,
        ruta_original=ruta_original,
        ruta_protegida=ruta_protegida,
        nivel_proteccion=nivel_proteccion,
        proteccion_ia_activa=datos_blindaje["proteccion_ia_activa"],
        marca_invisible_activa=datos_blindaje["marca_invisible_activa"],
        estado="En revisión" if es_sospechosa else "Protegida",
        obra_inspirada_id=obra_inspirada_id if obra_inspirada_id and obra_inspirada_id > 0 else None,
        es_sospechosa=es_sospechosa,
        motivo_sospecha=motivo_sospecha if es_sospechosa else None,
        estado_moderacion="Pendiente" if es_sospechosa else "Aprobada",
        autor_id=usuario_actual.id
    )
    bd.add(nueva_obra)
    bd.flush()

    nueva_huella = HuellaObra(
        obra_id=nueva_obra.id,
        hash_sha256=datos_blindaje["hash_sha256"],
        hash_phash=phash,
        hash_dhash=dhash,
        firma_dct_dwt=datos_blindaje["firma_dct_dwt"],
        embedding_clip_json=json.dumps(vector_clip)
    )
    bd.add(nueva_huella)

    # Paso 6: Registrar evidencia en el Smart Contract de la Blockchain Local (Hardhat)
    datos_bc = registrar_obra_en_blockchain(
        codigo_obra=codigo_obra,
        hash_sha256=datos_blindaje["hash_sha256"],
        nombre_autor=usuario_actual.nombre_apellido
    )

    registro_bc = RegistroBlockchain(
        codigo_certificado=codigo_certificado,
        obra_id=nueva_obra.id,
        hash_sha256_registrado=datos_blindaje["hash_sha256"],
        hash_transaccion=datos_bc["hash_transaccion"],
        direccion_contrato=datos_bc["direccion_contrato"],
        numero_bloque=datos_bc["numero_bloque"],
        red_blockchain=datos_bc["red_blockchain"]
    )
    bd.add(registro_bc)

    # Si fue clasificada como sospechosa (US-09), enviar notificación automática a todos los moderadores activos
    if es_sospechosa:
        moderadores = bd.query(Usuario).filter(Usuario.rol.in_(["moderador", "dueno"])).all()
        for mod in moderadores:
            bd.add(Notificacion(
                usuario_destino_id=mod.id,
                rol_destino="moderador",
                titulo=f"Obra sospechosa detectada: {codigo_obra}",
                mensaje=motivo_sospecha,
                tipo="sospechosa",
                referencia_codigo=codigo_obra
            ))

    bd.commit()
    bd.refresh(nueva_obra)

    return {
        "mensaje": "Obra protegida y registrada exitosamente en la blockchain.",
        "pasos_completados": [
            "Archivo verificado",
            "Huella digital generada",
            "Marca invisible integrada",
            "Registro de autoría",
            "Monitoreo preparado"
        ],
        "evaluacion_ia": resultado_ml,
        "almacenamiento_nube": info_r2,
        "obra": {
            "id": nueva_obra.id,
            "codigo_obra": nueva_obra.codigo_obra,
            "titulo": nueva_obra.titulo,
            "estado": nueva_obra.estado,
            "fecha_registro": formatear_fecha_es(nueva_obra.fecha_registro, "largo"),
            "proteccion_ia": "Activada" if nueva_obra.proteccion_ia_activa else "No aplicada",
            "marca_invisible": "Integrada",
            "hash_corto": datos_blindaje["hash_sha256"][:18],
            "hash_sha256": datos_blindaje["hash_sha256"],
            "codigo_certificado": codigo_certificado,
            "tx_blockchain": datos_bc["hash_transaccion"],
            "obra_inspirada_en": nueva_obra.obra_inspirada_en.titulo if nueva_obra.obra_inspirada_en else None,
            "es_sospechosa": nueva_obra.es_sospechosa,
            "motivo_sospecha": nueva_obra.motivo_sospecha,
            "evaluacion_ia": resultado_ml,
            "url_imagen": f"http://localhost:8000/archivos/protegidas/{nombre_seguro}"
        }
    }


@enrutador.get("/{obra_id}")
def obtener_detalle_obra(obra_id: int, bd: Session = Depends(obtener_bd)):
    """
    US-03 y US-04: Devuelve el detalle técnico de una obra protegida (como 'Mau Feliz')
    y los datos de su Certificado Digital de Autoría.
    """
    obra = bd.query(Obra).filter(Obra.id == obra_id).first()
    if not obra:
        raise HTTPException(status_code=404, detail="La obra solicitada no existe.")

    verificacion_onchain = consultar_obra_en_blockchain(obra.codigo_obra)

    return {
        "id": obra.id,
        "codigo_obra": obra.codigo_obra,
        "titulo": obra.titulo,
        "descripcion": obra.descripcion,
        "autor": obra.autor.nombre_apellido if obra.autor else "Nayeli Castillo",
        "estado": obra.estado,
        "es_sospechosa": obra.es_sospechosa,
        "motivo_sospecha": obra.motivo_sospecha,
        "estado_moderacion": obra.estado_moderacion,
        "fecha_registro": formatear_fecha_es(obra.fecha_registro, "largo"),
        "proteccion_contra_ia": "Activada" if obra.proteccion_ia_activa else "Ligera",
        "marca_invisible": "Integrada" if obra.marca_invisible_activa else "No",
        "hash_sha256": obra.huella.hash_sha256 if obra.huella else "",
        "hash_corto": obra.huella.hash_sha256[:18] if obra.huella else "0x8f72a9c4e6b031d5",
        "firma_dct_dwt": obra.huella.firma_dct_dwt if obra.huella else "",
        "obra_inspirada_titulo": obra.obra_inspirada_en.titulo if obra.obra_inspirada_en else None,
        "url_imagen": f"http://localhost:8000/archivos/protegidas/{os.path.basename(obra.ruta_protegida or obra.ruta_original)}",
        "certificado": {
            "codigo_certificado": obra.registro_blockchain.codigo_certificado if obra.registro_blockchain else "AEG-2026-0024",
            "hash_transaccion": obra.registro_blockchain.hash_transaccion if obra.registro_blockchain else "0x3ac9...e720",
            "direccion_contrato": obra.registro_blockchain.direccion_contrato if obra.registro_blockchain else "",
            "numero_bloque": obra.registro_blockchain.numero_bloque if obra.registro_blockchain else 1,
            "verificado_en_nodo_hardhat": verificacion_onchain is not None
        }
    }