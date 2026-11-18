import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


# ================= US-01 y US-07: AUTENTICACIÓN Y PERFIL =================
class RegistroUsuarioSolicitud(BaseModel):
    nombre_apellido: str = Field(..., min_length=2, max_length=120)
    dni: str = Field(...)
    correo: EmailStr
    celular: str = Field(...)
    contrasena: str = Field(..., min_length=8, max_length=100)

    @field_validator("dni")
    @classmethod
    def validar_dni_peru(cls, v: str) -> str:
        limpio = v.strip()
        if not re.fullmatch(r"\d{8}", limpio):
            raise ValueError("Ingresa 8 dígitos, sin espacios.")
        return limpio

    @field_validator("celular")
    @classmethod
    def validar_celular_peru(cls, v: str) -> str:
        limpio = re.sub(r"\s+", "", v)
        if clean := re.sub(r"^\+51", "", limpio):
            if re.fullmatch(r"9\d{8}", clean):
                return f"+51 {clean[:3]} {clean[3:6]} {clean[6:]}"
        raise ValueError("Ingresa 9 dígitos después de +51, empezando por 9.")


class InicioSesionSolicitud(BaseModel):
    correo: EmailStr
    contrasena: str


class RecuperarCuentaSolicitud(BaseModel):
    correo: EmailStr


class CambiarContrasenaSolicitud(BaseModel):
    correo: EmailStr
    nueva_contrasena: str = Field(..., min_length=8, max_length=100)
    token_recuperacion: Optional[str] = None


class ActualizarPerfilSolicitud(BaseModel):
    nombre_apellido: str = Field(..., min_length=2, max_length=120)
    correo: EmailStr
    especialidad: str = Field(default="Artista digital", max_length=80)
    nueva_contrasena: Optional[str] = None


# ================= US-06: PLANES DE SUSCRIPCIÓN =================
class PlanSuscripcionSolicitud(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=40)
    descripcion: str = Field(..., min_length=1, max_length=200)
    precio: float = Field(..., ge=0.0, le=9999.99)
    moneda: str = Field(default="PEN")
    periodicidad: str = Field(...)
    obras_protegidas: int = Field(..., gt=0, le=1000)
    obras_monitoreo: int = Field(..., gt=0, le=1000)
    frecuencia_monitoreo: str = Field(...)
    estado: str = Field(default="Activo")

    @field_validator("obras_monitoreo")
    @classmethod
    def validar_limite_monitoreo(cls, v: int, info) -> int:
        protegidas = info.data.get("obras_protegidas")
        if protegidas is not None and v > protegidas:
            raise ValueError("Indica cuántas obras se monitorearán. No debe superar las protegidas.")
        return v


# ================= US-05: MONITOREO POR URL TEMPORAL =================
class EscanearUrlSolicitud(BaseModel):
    url_temporal: str = Field(..., min_length=5, max_length=500)
    obra_id: Optional[int] = None


class ActualizarEstadoCoincidenciaSolicitud(BaseModel):
    estado_artista: str  # Confirmado | Descartado | Reclamo


# ================= US-10: MODERACIÓN =================
class DecisionModeradorSolicitud(BaseModel):
    decision: str  # Aceptada | Rechazada | Aprobada | Reportada
    comentarios: Optional[str] = ""