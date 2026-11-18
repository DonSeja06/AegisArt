from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from aplicacion.nucleo.base_datos import obtener_bd
from aplicacion.modelos.modelos_bd import PlanSuscripcion
from aplicacion.esquemas.esquemas_api import PlanSuscripcionSolicitud

enrutador = APIRouter(prefix="/api/planes", tags=["Gestión de Planes de Suscripción (US-06)"])


@enrutador.get("")
def listar_planes(
    buscar: Optional[str] = None,
    estado: Optional[str] = None,
    periodicidad: Optional[str] = None,
    bd: Session = Depends(obtener_bd)
):
    """
    US-06: Lista todos los planes registrados (Junior, Inicial, Creador, Profesional)
    con filtros por texto, estado y periodicidad.
    """
    consulta = bd.query(PlanSuscripcion)
    if buscar and buscar.strip():
        consulta = consulta.filter(PlanSuscripcion.nombre.ilike(f"%{buscar.strip()}%"))
    if estado and estado not in ("Todos los estados", "Todos"):
        consulta = consulta.filter(PlanSuscripcion.estado == estado)
    if periodicidad and periodicidad not in ("Todas las periodicidades", "Todas"):
        consulta = consulta.filter(PlanSuscripcion.periodicidad == periodicidad)

    planes = consulta.order_by(PlanSuscripcion.precio.asc()).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "precio_formateado": "Gratuito" if p.precio == 0 else f"S/{p.precio:.2f}",
            "moneda": p.moneda,
            "periodicidad": p.periodicidad,
            "obras_protegidas": p.obras_protegidas,
            "obras_monitoreo": p.obras_monitoreo,
            "frecuencia_monitoreo": p.frecuencia_monitoreo,
            "estado": p.estado
        }
        for p in planes
    ]


@enrutador.get("/{plan_id}")
def obtener_plan(plan_id: int, bd: Session = Depends(obtener_bd)):
    plan = bd.query(PlanSuscripcion).filter(PlanSuscripcion.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado.")
    return {
        "id": plan.id,
        "nombre": plan.nombre,
        "descripcion": plan.descripcion,
        "precio": plan.precio,
        "moneda": plan.moneda,
        "periodicidad": plan.periodicidad,
        "obras_protegidas": plan.obras_protegidas,
        "obras_monitoreo": plan.obras_monitoreo,
        "frecuencia_monitoreo": plan.frecuencia_monitoreo,
        "estado": plan.estado
    }


@enrutador.post("")
def crear_nuevo_plan(datos: PlanSuscripcionSolicitud, bd: Session = Depends(obtener_bd)):
    """
    US-06: Crea un nuevo plan de suscripción validando campos obligatorios y límites.
    """
    if bd.query(PlanSuscripcion).filter(PlanSuscripcion.nombre.ilike(datos.nombre.strip())).first():
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre.")

    nuevo = PlanSuscripcion(
        nombre=datos.nombre.strip(),
        descripcion=datos.descripcion.strip(),
        precio=round(datos.precio, 2),
        moneda=datos.moneda,
        periodicidad=datos.periodicidad,
        obras_protegidas=datos.obras_protegidas,
        obras_monitoreo=datos.obras_monitoreo,
        frecuencia_monitoreo=datos.frecuencia_monitoreo,
        estado=datos.estado
    )
    bd.add(nuevo)
    bd.commit()
    bd.refresh(nuevo)

    return {
        "mensaje": f"El plan {nuevo.nombre} se ha creado correctamente.",
        "plan": {
            "id": nuevo.id,
            "nombre": nuevo.nombre,
            "descripcion": nuevo.descripcion,
            "precio": nuevo.precio,
            "moneda": nuevo.moneda,
            "periodicidad": nuevo.periodicidad,
            "obras_protegidas": nuevo.obras_protegidas,
            "obras_monitoreo": nuevo.obras_monitoreo,
            "frecuencia_monitoreo": nuevo.frecuencia_monitoreo,
            "estado": nuevo.estado
        }
    }


@enrutador.put("/{plan_id}")
def actualizar_plan_existente(
    plan_id: int,
    datos: PlanSuscripcionSolicitud,
    bd: Session = Depends(obtener_bd)
):
    """
    US-06: Actualiza los precios, límites de protección, monitoreo y estado de un plan existente.
    """
    plan = bd.query(PlanSuscripcion).filter(PlanSuscripcion.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="El plan que intentas actualizar no existe.")

    plan.nombre = datos.nombre.strip()
    plan.descripcion = datos.descripcion.strip()
    plan.precio = round(datos.precio, 2)
    plan.moneda = datos.moneda
    plan.periodicidad = datos.periodicidad
    plan.obras_protegidas = datos.obras_protegidas
    plan.obras_monitoreo = datos.obras_monitoreo
    plan.frecuencia_monitoreo = datos.frecuencia_monitoreo
    plan.estado = datos.estado

    bd.commit()
    bd.refresh(plan)

    return {
        "mensaje": f"El plan {plan.nombre} se ha actualizado correctamente.",
        "plan": {
            "id": plan.id,
            "nombre": plan.nombre,
            "descripcion": plan.descripcion,
            "precio": plan.precio,
            "moneda": plan.moneda,
            "periodicidad": plan.periodicidad,
            "obras_protegidas": plan.obras_protegidas,
            "obras_monitoreo": plan.obras_monitoreo,
            "frecuencia_monitoreo": plan.frecuencia_monitoreo,
            "estado": plan.estado
        }
    }