import os
from dotenv import load_dotenv

# Carga automáticamente las variables del archivo .env
load_dotenv()

class Configuracion:
    NOMBRE_PROYECTO: str = "AegisArt - Plataforma de Defensa contra IA y Certificado de Autoría"
    VERSION: str = "2.0.0 - Sprint 2 (APF3)"
    
    URL_BASE_DATOS: str = os.getenv(
        "URL_BASE_DATOS",
        "postgresql+psycopg2://postgres:123456@localhost:5432/aegisart_bd"
    )
    
    CLAVE_SECRETA_JWT: str = os.getenv("CLAVE_SECRETA_JWT", "clave_super_secreta_aegisart_utp_2026")
    ALGORITMO_JWT: str = "HS256"
    MINUTOS_EXPIRACION_TOKEN: int = 60 * 24
    MINUTOS_RECUPERACION_CORREO: int = 15

    URL_NODO_HARDHAT: str = os.getenv("URL_NODO_HARDHAT", "http://127.0.0.1:8545")
    DIRECCION_CONTRATO: str = os.getenv(
        "DIRECCION_CONTRATO",
        "0x5FbDB2315678afecb367f032d93F642f64180aa3"
    )

    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "aegisart-obras-cloud")
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")

configuracion = Configuracion()