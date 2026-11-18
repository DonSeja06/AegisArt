from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from aplicacion.nucleo.base_datos import obtener_bd
from aplicacion.nucleo.utilidades import formatear_fecha_es
from aplicacion.modelos.modelos_bd import (
    Usuario, Obra, Coincidencia, PlanSuscripcion, RegistroBlockchain, Notificacion
)
from aplicacion.esquemas.esquemas_api import DecisionModeradorSolicitud
from aplicacion.servicios.servicio_ia_apf3 import obtener_metricas_modelo_apf3

enrutador = APIRouter(
    prefix="/api/moderacion-admin",
    tags=["Moderación y Estadísticas del Dueño (US-09, US-10, US-12)"]
)


@enrutador.get("/casos")
def listar_casos_y_obras_sospechosas(bd: Session = Depends(obtener_bd)):
    """
    US-09 y US-10: Devuelve los casos enviados a revisión (ej. AEG-003) y las obras
    digitales marcadas como sospechosas por el algoritmo al subirse, junto con las alertas del moderador.
    """
    casos_apelacion = bd.query(Coincidencia).filter(
        Coincidencia.enviado_a_moderacion == True
    ).order_by(Coincidencia.id.desc()).all()

    obras_sospechosas = bd.query(Obra).filter(
        Obra.es_sospechosa == True
    ).order_by(Obra.id.desc()).all()

    notificaciones_mod = bd.query(Notificacion).filter(
        Notificacion.rol_destino == "moderador"
    ).order_by(Notificacion.fecha_creacion.desc()).limit(10).all()

    return {
        "casos_en_revision": [
            {
                "id": c.id,
                "codigo_caso": c.codigo_caso.replace("2026-", ""),  # Ej: AEG-003 como en Figma
                "codigo_completo": c.codigo_caso,
                "obra_titulo": c.obra_original.titulo,
                "autor": c.obra_original.autor.nombre_apellido if c.obra_original.autor else "Nayeli Castillo",
                "similitud": c.porcentaje_similitud,
                "motivo": c.motivo_reporte,
                "marca_invisible_detectada": c.marca_invisible_identificada,
                "fecha_registro_previo": formatear_fecha_es(c.obra_original.fecha_registro, "largo"),
                "fecha": formatear_fecha_es(c.fecha_deteccion, "corto_coma"),
                "estado_moderador": c.estado_moderador,
                "comentarios_moderador": c.comentarios_moderador or ""
            }
            for c in casos_apelacion
        ],
        "obras_sospechosas": [
            {
                "id": o.id,
                "codigo_obra": o.codigo_obra,
                "titulo": o.titulo,
                "autor": o.autor.nombre_apellido if o.autor else "Artista",
                "motivo_sospecha": o.motivo_sospecha,
                "estado_moderacion": o.estado_moderacion,
                "comentario_moderador": o.comentario_moderador or "",
                "fecha": formatear_fecha_es(o.fecha_registro, "corto_coma")
            }
            for o in obras_sospechosas
        ],
        "notificaciones_moderador": [
            {
                "id": n.id,
                "titulo": n.titulo,
                "mensaje": n.mensaje,
                "referencia_codigo": n.referencia_codigo,
                "fecha": n.fecha_creacion.strftime("%d/%m/%Y %H:%M")
            }
            for n in notificaciones_mod
        ]
    }


@enrutador.put("/casos/{caso_id}/resolver")
def resolver_apelacion_moderador(
    caso_id: int,
    datos: DecisionModeradorSolicitud,
    bd: Session = Depends(obtener_bd)
):
    """
    US-10: Permite al moderador 'Aceptar apelación' o 'Rechazar apelación' registrando sus comentarios.
    """
    caso = bd.query(Coincidencia).filter(Coincidencia.id == caso_id).first()
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")

    caso.estado_moderador = datos.decision
    caso.comentarios_moderador = datos.comentarios
    if caso.obra_original and caso.obra_original.autor_id:
        bd.add(Notificacion(
            usuario_destino_id=caso.obra_original.autor_id,
            rol_destino="artista",
            titulo=f"Resolución de moderación: {caso.codigo_caso}",
            mensaje=f"Tu caso sobre '{caso.obra_original.titulo}' fue marcado como '{datos.decision}'.",
            tipo="moderacion",
            referencia_codigo=caso.codigo_caso
        ))
    bd.commit()

    return {
        "mensaje": f"El caso {caso.codigo_caso} ha sido marcado como '{datos.decision}'."
    }


@enrutador.put("/obras-sospechosas/{obra_id}/revisar")
def revisar_obra_sospechosa(
    obra_id: int,
    datos: DecisionModeradorSolicitud,
    bd: Session = Depends(obtener_bd)
):
    """
    US-10: Permite al moderador aprobar, rechazar o reportar una obra clasificada como sospechosa.
    """
    obra = bd.query(Obra).filter(Obra.id == obra_id).first()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra sospechosa no encontrada.")

    obra.estado_moderacion = datos.decision  # Aprobada | Rechazada | Reportada
    obra.comentario_moderador = datos.comentarios
    if datos.decision == "Aprobada":
        obra.es_sospechosa = False
        obra.estado = "Protegida"
    elif datos.decision in ("Rechazada", "Reportada"):
        obra.estado = "Rechazada"

    if obra.autor_id:
        bd.add(Notificacion(
            usuario_destino_id=obra.autor_id,
            rol_destino="artista",
            titulo=f"Revisión completada ({obra.codigo_obra})",
            mensaje=f"Moderación marcó tu obra '{obra.titulo}' como '{datos.decision}'.",
            tipo="moderacion",
            referencia_codigo=obra.codigo_obra
        ))

    bd.commit()
    return {
        "mensaje": f"La obra '{obra.titulo}' fue {datos.decision.lower()} por moderación."
    }


@enrutador.get("/metricas-dueno")
def obtener_metricas_crecimiento_dueno(bd: Session = Depends(obtener_bd)):
    """
    US-12: Como dueño de la aplicación, permite consultar la cantidad de artistas
    y obras registradas para evaluar el crecimiento y alcance de AegisArt.
    """
    total_artistas = bd.query(Usuario).filter(Usuario.rol == "artista").count()
    total_usuarios = bd.query(Usuario).count()
    total_obras = bd.query(Obra).count()
    total_certificados = bd.query(RegistroBlockchain).count()
    total_coincidencias = bd.query(Coincidencia).count()
    planes_activos = bd.query(PlanSuscripcion).filter(PlanSuscripcion.estado == "Activo").count()

    return {
        "total_artistas_registrados": total_artistas,
        "total_usuarios_plataforma": total_usuarios,
        "total_obras_registradas": total_obras,
        "total_certificados_blockchain": total_certificados,
        "total_coincidencias_detectadas": total_coincidencias,
        "planes_activos": planes_activos,
        "crecimiento_mensual": [
            {"mes": "Mayo 2026", "artistas": 1, "obras": 2},
            {"mes": "Junio 2026", "artistas": 2, "obras": 5},
            {"mes": "Octubre 2026", "artistas": total_artistas, "obras": total_obras}
        ]
    }

@enrutador.get("/metricas-ia-apf3")
def consultar_metricas_ia_apf3():
    """
    Capítulo 2 del APF3 (Ruta A): Devuelve las métricas de evaluación del Árbol de Decisión
    entrenado con scikit-learn (80% entrenamiento / 20% prueba).
    """
    return obtener_metricas_modelo_apf3()