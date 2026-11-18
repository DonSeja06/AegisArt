import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from aplicacion.nucleo.base_datos import obtener_bd
from aplicacion.nucleo.configuracion import configuracion
from aplicacion.nucleo.seguridad import (
    encriptar_contrasena,
    verificar_contrasena,
    crear_token_acceso,
    obtener_usuario_actual
)
from aplicacion.modelos.modelos_bd import Usuario, PlanSuscripcion, Obra
from aplicacion.esquemas.esquemas_api import (
    RegistroUsuarioSolicitud,
    InicioSesionSolicitud,
    RecuperarCuentaSolicitud,
    CambiarContrasenaSolicitud,
    ActualizarPerfilSolicitud
)

enrutador = APIRouter(prefix="/api/autenticacion", tags=["Autenticación y Perfil (US-01, US-07)"])


@enrutador.post("/registro")
def registrar_usuario(datos: RegistroUsuarioSolicitud, bd: Session = Depends(obtener_bd)):
    """
    US-01: Crea una cuenta personal para acceder de manera segura a AegisArt.
    """
    correo_limpio = datos.correo.strip().lower()
    if bd.query(Usuario).filter(Usuario.correo == correo_limpio).first():
        raise HTTPException(status_code=400, detail="Este correo electrónico ya se encuentra registrado.")

    if bd.query(Usuario).filter(Usuario.dni == datos.dni.strip()).first():
        raise HTTPException(status_code=400, detail="Este número de DNI ya se encuentra registrado.")

    plan_base = bd.query(PlanSuscripcion).filter(PlanSuscripcion.nombre == "Creador").first()

    nuevo_usuario = Usuario(
        nombre_apellido=datos.nombre_apellido.strip(),
        dni=datos.dni.strip(),
        correo=correo_limpio,
        celular=datos.celular,
        contrasena_hash=encriptar_contrasena(datos.contrasena.strip()),
        especialidad="Artista digital",
        rol="artista",
        plan_id=plan_base.id if plan_base else None
    )
    bd.add(nuevo_usuario)
    bd.commit()
    bd.refresh(nuevo_usuario)

    token = crear_token_acceso({"sub": nuevo_usuario.correo, "rol": nuevo_usuario.rol})

    return {
        "mensaje": f"Bienvenida, {nuevo_usuario.nombre_apellido.split()[0]}. Tu cuenta de AegisArt se creó correctamente. Ya puedes empezar a proteger tus obras.",
        "token_acceso": token,
        "usuario": {
            "id": nuevo_usuario.id,
            "nombre_apellido": nuevo_usuario.nombre_apellido,
            "dni": nuevo_usuario.dni,
            "correo": nuevo_usuario.correo,
            "celular": nuevo_usuario.celular,
            "especialidad": nuevo_usuario.especialidad,
            "rol": nuevo_usuario.rol
        }
    }


@enrutador.post("/iniciar-sesion")
def iniciar_sesion(datos: InicioSesionSolicitud, bd: Session = Depends(obtener_bd)):
    """
    US-01: Inicio de sesión con correo y contraseña.
    Si la base de datos está vacía tras reiniciar la PC, carga las semillas automáticamente.
    """
    correo_limpio = datos.correo.strip().lower()
    clave_limpia = datos.contrasena.strip()

    # Si aún no existen usuarios en la BD, ejecutar la carga inicial automáticamente
    if bd.query(Usuario).count() == 0:
        from inicializar_bd import inicializar_datos
        inicializar_datos()

    usuario = bd.query(Usuario).filter(Usuario.correo == correo_limpio).first()
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Correo electrónico o contraseña incorrectos."
        )

    es_valida = verificar_contrasena(clave_limpia, usuario.contrasena_hash)

    # Garantizar acceso a las 3 cuentas semilla del prototipo con la clave 'aegisart123'
    correos_semilla = {"nayelis@gmail.com", "moderador@aegisart.pe", "admin@aegisart.pe"}
    if not es_valida and correo_limpio in correos_semilla and clave_limpia == "aegisart123":
        usuario.contrasena_hash = encriptar_contrasena("aegisart123")
        bd.commit()
        es_valida = True

    if not es_valida:
        raise HTTPException(
            status_code=401,
            detail="Correo electrónico o contraseña incorrectos."
        )

    token = crear_token_acceso({"sub": usuario.correo, "rol": usuario.rol})
    return {
        "mensaje": "Te damos la bienvenida",
        "token_acceso": token,
        "usuario": {
            "id": usuario.id,
            "nombre_apellido": usuario.nombre_apellido,
            "dni": usuario.dni,
            "correo": usuario.correo,
            "celular": usuario.celular,
            "especialidad": usuario.especialidad,
            "rol": usuario.rol
        }
    }


@enrutador.post("/recuperar-cuenta")
def solicitar_recuperacion_cuenta(datos: RecuperarCuentaSolicitud, bd: Session = Depends(obtener_bd)):
    """
    US-07: Solicita recuperación de contraseña generando un enlace/token válido por 15 minutos.
    """
    usuario = bd.query(Usuario).filter(Usuario.correo == datos.correo.strip().lower()).first()
    token_generado = None

    if usuario:
        token_generado = f"REC-{uuid.uuid4().hex[:8].upper()}"
        usuario.token_recuperacion = token_generado
        usuario.expiracion_token = datetime.utcnow() + timedelta(
            minutes=configuracion.MINUTOS_RECUPERACION_CORREO
        )
        bd.commit()

    return {
        "mensaje": "Si el correo está registrado, recibirás un enlace válido durante 15 minutos.",
        "token_demo_prototipo": token_generado
    }


@enrutador.post("/restablecer-contrasena")
def restablecer_contrasena(datos: CambiarContrasenaSolicitud, bd: Session = Depends(obtener_bd)):
    """
    US-07: Permite restablecer o actualizar la contraseña para recuperar acceso a obras y certificados.
    """
    usuario = bd.query(Usuario).filter(Usuario.correo == datos.correo.strip().lower()).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No se encontró una cuenta asociada a ese correo.")

    if not datos.token_recuperacion or not usuario.token_recuperacion or usuario.token_recuperacion != datos.token_recuperacion:
        raise HTTPException(status_code=400, detail="El código o enlace de recuperación es obligatorio o no es válido.")
    if usuario.expiracion_token and datetime.utcnow() > usuario.expiracion_token:
        raise HTTPException(status_code=400, detail="El enlace de recuperación ha expirado (15 minutos).")

    usuario.contrasena_hash = encriptar_contrasena(datos.nueva_contrasena.strip())
    usuario.token_recuperacion = None
    usuario.expiracion_token = None
    bd.commit()

    return {"mensaje": "Tu contraseña ha sido actualizada correctamente. Ya puedes iniciar sesión."}


@enrutador.get("/perfil")
def obtener_perfil(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    Obtiene los datos para la pantalla 'Tu perfil creativo' y la barra lateral.
    """
    total_obras = bd.query(Obra).filter(Obra.autor_id == usuario_actual.id).count()
    plan = usuario_actual.plan
    return {
        "id": usuario_actual.id,
        "nombre_apellido": usuario_actual.nombre_apellido,
        "iniciales": "".join([p[0].upper() for p in usuario_actual.nombre_apellido.split()[:2]]),
        "dni": usuario_actual.dni,
        "correo": usuario_actual.correo,
        "celular": usuario_actual.celular,
        "especialidad": usuario_actual.especialidad,
        "rol": usuario_actual.rol,
        "obras_protegidas_actuales": total_obras,
        "limite_obras_plan": 50 if not plan else plan.obras_protegidas,
        "nombre_plan": plan.nombre if plan else "Creador",
        "precio_plan": plan.precio if plan else 39.90,
        "periodicidad_plan": plan.periodicidad if plan else "Mensual",
        "metodo_pago_resumen": usuario_actual.metodo_pago_resumen,
        "proxima_renovacion": usuario_actual.proxima_renovacion
    }


@enrutador.put("/perfil")
def actualizar_perfil(
    datos: ActualizarPerfilSolicitud,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    bd: Session = Depends(obtener_bd)
):
    """
    US-07: Actualiza los datos en 'Tu perfil creativo' y permite cambiar la contraseña desde Configuración.
    """
    nuevo_correo = datos.correo.strip().lower()
    if nuevo_correo != usuario_actual.correo and bd.query(Usuario).filter(Usuario.correo == nuevo_correo).first():
        raise HTTPException(status_code=400, detail="Este correo electrónico ya está en uso por otra cuenta.")
    usuario_actual.nombre_apellido = datos.nombre_apellido.strip()
    usuario_actual.correo = nuevo_correo
    usuario_actual.especialidad = datos.especialidad.strip()

    if datos.nueva_contrasena and len(datos.nueva_contrasena.strip()) >= 8:
        usuario_actual.contrasena_hash = encriptar_contrasena(datos.nueva_contrasena.strip())

    bd.commit()
    return {"mensaje": "Cambios guardados correctamente en tu perfil creativo."}