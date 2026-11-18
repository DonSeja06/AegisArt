from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from aplicacion.nucleo.configuracion import configuracion

motor_bd = create_engine(configuracion.URL_BASE_DATOS, echo=False)
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor_bd)
Base = declarative_base()

def obtener_bd():
    bd = SesionLocal()
    try:
        yield bd
    finally:
        bd.close()