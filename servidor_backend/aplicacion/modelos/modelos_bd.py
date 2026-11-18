from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from aplicacion.nucleo.base_datos import Base


class PlanSuscripcion(Base):
    __tablename__ = "planes_suscripcion"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(40), unique=True, nullable=False)
    descripcion = Column(String(200), nullable=False)
    precio = Column(Float, nullable=False, default=0.0)
    moneda = Column(String(10), nullable=False, default="PEN")
    periodicidad = Column(String(20), nullable=False, default="Mensual")
    obras_protegidas = Column(Integer, nullable=False, default=50)
    obras_monitoreo = Column(Integer, nullable=False, default=10)
    frecuencia_monitoreo = Column(String(30), nullable=False, default="Semanal")
    estado = Column(String(15), nullable=False, default="Activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuarios = relationship("Usuario", back_populates="plan")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_apellido = Column(String(120), nullable=False)
    dni = Column(String(8), unique=True, nullable=False)
    correo = Column(String(120), unique=True, index=True, nullable=False)
    celular = Column(String(20), nullable=False)
    contrasena_hash = Column(String(255), nullable=False)
    especialidad = Column(String(80), default="Artista digital")
    rol = Column(String(20), default="artista")  # artista | moderador | dueno
    
    # Suscripción activa (US-06)
    plan_id = Column(Integer, ForeignKey("planes_suscripcion.id"), nullable=True)
    metodo_pago_resumen = Column(String(100), default="Visa terminada en 4821 · vence 10/27")
    proxima_renovacion = Column(String(30), default="18 nov 2026")

    # Recuperación de cuenta (US-07)
    token_recuperacion = Column(String(100), nullable=True)
    expiracion_token = Column(DateTime, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    plan = relationship("PlanSuscripcion", back_populates="usuarios")
    obras = relationship("Obra", back_populates="autor")
    notificaciones = relationship("Notificacion", back_populates="usuario_destino")
    escaneos_url = relationship("EscaneoUrl", back_populates="usuario")


class Obra(Base):
    __tablename__ = "obras"

    id = Column(Integer, primary_key=True, index=True)
    codigo_obra = Column(String(30), unique=True, index=True, nullable=False)  # Ej: OBRA-001
    titulo = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    nombre_archivo = Column(String(255), nullable=False)
    formato = Column(String(10), nullable=False)  # PNG, JPG, WEBP
    tamano_mb = Column(Float, nullable=False)
    ruta_original = Column(String(500), nullable=False)
    ruta_protegida = Column(String(500), nullable=True)
    
    # Nivel de protección elegido (US-03): Equilibrada | Maxima | Ligera
    nivel_proteccion = Column(String(30), default="Equilibrada")
    proteccion_ia_activa = Column(Boolean, default=True)
    marca_invisible_activa = Column(Boolean, default=True)
    
    # Estados en Galería (US-04): Protegida | Monitoreando | Coincidencia encontrada
    estado = Column(String(35), default="Protegida")
    
    # Declaración de obra inspirada en otra ya subida (US-08)
    obra_inspirada_id = Column(Integer, ForeignKey("obras.id"), nullable=True)
    
    # Clasificación de obra sospechosa para moderadores (US-09 y US-10)
    es_sospechosa = Column(Boolean, default=False)
    motivo_sospecha = Column(String(255), nullable=True)
    estado_moderacion = Column(String(25), default="Aprobada")  # Aprobada | Pendiente | Rechazada | Reportada
    comentario_moderador = Column(Text, nullable=True)

    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    autor = relationship("Usuario", back_populates="obras")
    obra_inspirada_en = relationship("Obra", remote_side=[id], backref="obras_derivadas")
    huella = relationship("HuellaObra", back_populates="obra", uselist=False, cascade="all, delete-orphan")
    registro_blockchain = relationship("RegistroBlockchain", back_populates="obra", uselist=False, cascade="all, delete-orphan")
    coincidencias = relationship("Coincidencia", back_populates="obra_original", cascade="all, delete-orphan")


class HuellaObra(Base):
    __tablename__ = "huellas_obras"

    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(Integer, ForeignKey("obras.id"), unique=True, nullable=False)
    hash_sha256 = Column(String(66), unique=True, index=True, nullable=False)
    hash_phash = Column(String(64), nullable=False)
    hash_dhash = Column(String(64), nullable=False)
    firma_dct_dwt = Column(String(120), nullable=False)
    embedding_clip_json = Column(Text, nullable=True)

    obra = relationship("Obra", back_populates="huella")


class RegistroBlockchain(Base):
    __tablename__ = "registros_blockchain"

    id = Column(Integer, primary_key=True, index=True)
    codigo_certificado = Column(String(30), unique=True, index=True, nullable=False)  # Ej: AEG-2026-0024
    obra_id = Column(Integer, ForeignKey("obras.id"), unique=True, nullable=False)
    hash_sha256_registrado = Column(String(66), nullable=False)
    hash_transaccion = Column(String(80), nullable=False)
    direccion_contrato = Column(String(60), nullable=False)
    numero_bloque = Column(Integer, default=1)
    red_blockchain = Column(String(40), default="Hardhat Local EVM")
    fecha_transaccion = Column(DateTime, default=datetime.utcnow)

    obra = relationship("Obra", back_populates="registro_blockchain")


class EscaneoUrl(Base):
    """
    Registra cada búsqueda/monitoreo puntual que el artista realiza ingresando
    una URL temporal en el prototipo (US-05).
    """
    __tablename__ = "escaneos_url"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    obra_objetivo_id = Column(Integer, ForeignKey("obras.id"), nullable=True)
    url_ingresada = Column(String(500), nullable=False)
    plataforma_detectada = Column(String(50), default="Sitio Web Externo")
    coincidencias_halladas = Column(Integer, default=0)
    mayor_similitud = Column(Float, default=0.0)
    estado_escaneo = Column(String(40), default="Completado")
    fecha_escaneo = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="escaneos_url")


class Coincidencia(Base):
    __tablename__ = "coincidencias"

    id = Column(Integer, primary_key=True, index=True)
    codigo_caso = Column(String(30), unique=True, index=True, nullable=False)  # Ej: AEG-2026-003
    obra_original_id = Column(Integer, ForeignKey("obras.id"), nullable=False)
    
    plataforma = Column(String(50), nullable=False)  # Instagram, Pinterest, URL Temporal, etc.
    url_detectada = Column(String(500), nullable=False)  # La URL temporal donde se encontró la copia
    ruta_imagen_copia = Column(String(500), nullable=True)
    
    porcentaje_similitud = Column(Float, nullable=False)  # Ej: 98.2
    similitud_visual_phash = Column(Float, default=95.0)
    similitud_semantica_clip = Column(Float, default=98.2)
    
    diferencias_detectadas = Column(
        String(255),
        default="Recorte de bordes · Ajuste de color · Firma original eliminada"
    )
    marca_invisible_identificada = Column(Boolean, default=True)
    hash_copia_detectada = Column(String(66), default="0x7e45b19c83d212c4")
    
    # Estados en vista Artista (US-05): Pendiente | Confirmado | Descartado
    estado_artista = Column(String(25), default="Pendiente")
    
    # Estados en vista Moderador (US-10): En revisión | Aceptada | Rechazada
    enviado_a_moderacion = Column(Boolean, default=False)
    motivo_reporte = Column(String(100), default="Uso sin autorización")
    estado_moderador = Column(String(25), default="En revisión")
    comentarios_moderador = Column(Text, nullable=True)
    
    fecha_deteccion = Column(DateTime, default=datetime.utcnow)

    obra_original = relationship("Obra", back_populates="coincidencias")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_destino_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    rol_destino = Column(String(20), default="artista")  # artista | moderador
    titulo = Column(String(120), nullable=False)
    mensaje = Column(String(255), nullable=False)
    tipo = Column(String(30), default="coincidencia")
    leida = Column(Boolean, default=False)
    referencia_codigo = Column(String(40), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario_destino = relationship("Usuario", back_populates="notificaciones")