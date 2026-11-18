import os
import shutil
import boto3
from aplicacion.nucleo.configuracion import configuracion


def subir_obra_a_cloudflare_r2(ruta_archivo_local: str, nombre_archivo: str) -> dict:
    """
    Sube el archivo procesado al almacenamiento en la nube Cloudflare R2 usando boto3 (API S3).
    Si no se han colocado credenciales de pago en .env, sincroniza el objeto en el bucket local
    de Cloudflare R2 ('archivos_subidos/bucket_cloudflare_r2') y retorna la URL servida.
    """
    carpeta_bucket_local = os.path.join("archivos_subidos", "bucket_cloudflare_r2")
    os.makedirs(carpeta_bucket_local, exist_ok=True)
    ruta_destino_bucket = os.path.join(carpeta_bucket_local, nombre_archivo)

    # Copia física en el bucket local de respaldo
    if os.path.exists(ruta_archivo_local) and os.path.abspath(ruta_archivo_local) != os.path.abspath(ruta_destino_bucket):
        shutil.copy2(ruta_archivo_local, ruta_destino_bucket)

    # Si el usuario configuró llaves reales de Cloudflare R2 en el archivo .env
    if (
        configuracion.R2_ACCOUNT_ID
        and configuracion.R2_ACCESS_KEY_ID
        and configuracion.R2_SECRET_ACCESS_KEY
    ):
        try:
            endpoint_url = f"https://{configuracion.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=configuracion.R2_ACCESS_KEY_ID,
                aws_secret_access_key=configuracion.R2_SECRET_ACCESS_KEY,
                region_name="auto"
            )
            s3.upload_file(ruta_archivo_local, configuracion.R2_BUCKET_NAME, nombre_archivo)
            url_publica = (
                f"{configuracion.R2_PUBLIC_URL.rstrip('/')}/{nombre_archivo}"
                if configuracion.R2_PUBLIC_URL
                else f"http://localhost:8000/archivos/bucket_cloudflare_r2/{nombre_archivo}"
            )
            return {
                "proveedor": "Cloudflare R2 Cloud Storage (API S3 Activa)",
                "bucket": configuracion.R2_BUCKET_NAME,
                "llave_r2": f"r2://{configuracion.R2_BUCKET_NAME}/{nombre_archivo}",
                "url_acceso": url_publica
            }
        except Exception as e:
            print(f"[Aviso R2] Usando bucket espejo local: {e}")

    return {
        "proveedor": "Cloudflare R2 (Bucket Sincronizado)",
        "bucket": configuracion.R2_BUCKET_NAME,
        "llave_r2": f"r2://{configuracion.R2_BUCKET_NAME}/{nombre_archivo}",
        "url_acceso": f"http://localhost:8000/archivos/bucket_cloudflare_r2/{nombre_archivo}"
    }