import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aplicacion.nucleo.configuracion import configuracion
from aplicacion.nucleo.base_datos import motor_bd, Base
from aplicacion.rutas import (
    rutas_autenticacion,
    rutas_obras,
    rutas_monitoreo,
    rutas_planes,
    rutas_moderacion_admin
)

# Asegurar que las tablas y carpetas de imágenes existan al arrancar
Base.metadata.create_all(bind=motor_bd)
os.makedirs("archivos_subidos/originales", exist_ok=True)
os.makedirs("archivos_subidos/protegidas", exist_ok=True)
os.makedirs("archivos_subidos/analizadas_url", exist_ok=True)

app = FastAPI(
    title=configuracion.NOMBRE_PROYECTO,
    version=configuracion.VERSION,
    description="API Backend en español para AegisArt (Sprints 1 y 2: US-01 a US-12)"
)

# Permitir peticiones desde el Frontend en Angular (puerto 4200)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir imágenes estáticas (originales, protegidas y descargadas por URL)
app.mount("/archivos", StaticFiles(directory="archivos_subidos"), name="archivos")

# Registrar los enrutadores de las 12 Historias de Usuario
app.include_router(rutas_autenticacion.enrutador)
app.include_router(rutas_obras.enrutador)
app.include_router(rutas_monitoreo.enrutador)
app.include_router(rutas_planes.enrutador)
app.include_router(rutas_moderacion_admin.enrutador)


@app.get("/")
def estado_servidor():
    return {
        "sistema": "AegisArt API",
        "estado": "Operativo",
        "alcance": "Sprint 1 y Sprint 2 (US-01 a US-12)"
    }