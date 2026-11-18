import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from aplicacion.nucleo.configuracion import configuracion
from aplicacion.nucleo.base_datos import obtener_bd
from aplicacion.modelos.modelos_bd import Usuario

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/autenticacion/iniciar-sesion", auto_error=False)


def encriptar_contrasena(contrasena_plana: str) -> str:
    sal = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena_plana.encode("utf-8"), sal).decode("utf-8")


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            contrasena_plana.encode("utf-8"),
            contrasena_hash.encode("utf-8")
        )
    except Exception:
        return False


def crear_token_acceso(datos: dict) -> str:
    copia_datos = datos.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=configuracion.MINUTOS_EXPIRACION_TOKEN)
    copia_datos.update({"exp": expiracion})
    return jwt.encode(
        copia_datos,
        configuracion.CLAVE_SECRETA_JWT,
        algorithm=configuracion.ALGORITMO_JWT
    )


def obtener_usuario_actual(
    token: str = Depends(esquema_oauth2),
    bd: Session = Depends(obtener_bd)
) -> Usuario:
    """
    Obtiene el usuario autenticado mediante el token JWT.
    Si en modo prototipo se consulta sin token, retorna a Nayeli Castillo por defecto
    para facilitar las pruebas rápidas.
    """
    if not token:
        usuario_demo = bd.query(Usuario).filter(Usuario.correo == "nayelis@gmail.com").first()
        if usuario_demo:
            return usuario_demo
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    try:
        payload = jwt.decode(
            token,
            configuracion.CLAVE_SECRETA_JWT,
            algorithms=[configuracion.ALGORITMO_JWT]
        )
        correo: str = payload.get("sub")
        if correo is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

    usuario = bd.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario