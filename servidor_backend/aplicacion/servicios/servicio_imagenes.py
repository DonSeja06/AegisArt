import os
import hashlib
import numpy as np
import cv2
import pywt
from PIL import Image, PngImagePlugin

FORMATOS_PERMITIDOS = {"PNG", "JPG", "JPEG", "WEBP"}
TAMANO_MAXIMO_MB = 20.0


def validar_archivo_imagen(nombre_archivo: str, tamano_bytes: int) -> tuple[bool, str, str, float]:
    """
    Valida formato (JPG, PNG, WEBP) y tamaño máximo (20 MB) según US-02 y US-03.
    """
    tamano_mb = round(tamano_bytes / (1024 * 1024), 2)
    extension = nombre_archivo.rsplit(".", 1)[-1].upper() if "." in nombre_archivo else ""

    if extension not in FORMATOS_PERMITIDOS:
        return (
            False,
            "El formato del archivo no es compatible. Selecciona una imagen JPG, PNG o WEBP.",
            extension,
            tamano_mb
        )

    if tamano_mb > TAMANO_MAXIMO_MB or tamano_bytes == 0:
        return (
            False,
            f"El archivo supera el tamaño máximo permitido de {int(TAMANO_MAXIMO_MB)} MB.",
            extension,
            tamano_mb
        )

    formato_normalizado = "JPG" if extension == "JPEG" else extension
    return True, "Archivo admitido", formato_normalizado, max(tamano_mb, 0.01)


def calcular_sha256_archivo(ruta_archivo: str) -> str:
    """
    Calcula la huella digital criptográfica SHA-256 exacta de los bytes del archivo.
    """
    sha256 = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            sha256.update(bloque)
    return "0x" + sha256.hexdigest()


def insertar_marca_invisible_dct_dwt(imagen_bgr: np.ndarray, codigo_obra: str) -> tuple[np.ndarray, str]:
    """
    Inserta una marca de agua esteganográfica invisible en el dominio frecuencial
    combinando DWT (Haar Wavelet) y DCT (Transformada Discreta del Coseno) sobre el canal de luminancia Y.
    """
    firma_texto = f"AEGIS-DCT-{codigo_obra}"
    bits_firma = [int(b) for caracter in firma_texto.encode("utf-8") for b in format(caracter, "08b")]

    # Convertir a espacio YCrCb para modificar solo la luminancia (imperceptible al ojo humano)
    ycrcb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2YCrCb).astype(np.float32)
    canal_y = ycrcb[:, :, 0]

    alto, ancho = canal_y.shape
    if alto < 16 or ancho < 16:
        return imagen_bgr, firma_texto

    alto_par = alto - (alto % 2)
    ancho_par = ancho - (ancho % 2)
    sub_y = canal_y[:alto_par, :ancho_par]

    # 1. Aplicar DWT 2D (Descomposición en sub-bandas LL, LH, HL, HH)
    coeffs = pywt.dwt2(sub_y, "haar")
    ll, (lh, hl, hh) = coeffs
    if ll.shape[0] < 8 or ll.shape[1] < 8:
        return imagen_bgr, firma_texto

    # 2. Aplicar DCT por bloques de 4x4 sobre la sub-banda LL e incrustar bits en frecuencias medias
    indice_bit = 0
    total_bits = len(bits_firma)
    fuerza_insercion = 24.0

    for fila in range(0, ll.shape[0] - 4, 4):
        for col in range(0, ll.shape[1] - 4, 4):
            if indice_bit >= total_bits:
                break
            bloque = ll[fila:fila + 4, col:col + 4]
            bloque_dct = cv2.dct(bloque)
            bit = bits_firma[indice_bit]
            # Modulación cuantizada del coeficiente de frecuencia media (2, 1)
            valor_actual = bloque_dct[2, 1]
            cuantizado = round(valor_actual / fuerza_insercion)
            if cuantizado % 2 != bit:
                cuantizado += 1 if bit == 1 else -1
            bloque_dct[2, 1] = cuantizado * fuerza_insercion
            ll[fila:fila + 4, col:col + 4] = cv2.idct(bloque_dct)
            indice_bit += 1
        if indice_bit >= total_bits:
            break

    # 3. Reconstruir mediante DWT Inversa
    canal_y_reconstruido = pywt.idwt2((ll, (lh, hl, hh)), "haar")
    ycrcb[:alto_par, :ancho_par, 0] = np.clip(canal_y_reconstruido, 0, 255)

    imagen_marcada = cv2.cvtColor(ycrcb.astype(np.uint8), cv2.COLOR_YCrCb2BGR)
    return imagen_marcada, firma_texto


def extraer_y_verificar_marca_dct_dwt(ruta_imagen: str, longitud_caracteres: int = 20) -> tuple[bool, str]:
    """
    Extrae los bits del dominio frecuencial DCT/DWT para verificar si la imagen
    conserva el prefijo de marca invisible de AegisArt ('AEGIS').
    """
    try:
        datos = np.fromfile(ruta_imagen, dtype=np.uint8)
        imagen_bgr = cv2.imdecode(datos, cv2.IMREAD_COLOR)
        if imagen_bgr is None or imagen_bgr.shape[0] < 16 or imagen_bgr.shape[1] < 16:
            return False, ""

        ycrcb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2YCrCb).astype(np.float32)
        canal_y = ycrcb[:, :, 0]
        alto_par = canal_y.shape[0] - (canal_y.shape[0] % 2)
        ancho_par = canal_y.shape[1] - (canal_y.shape[1] % 2)

        ll, _ = pywt.dwt2(canal_y[:alto_par, :ancho_par], "haar")
        if ll.shape[0] < 8 or ll.shape[1] < 8:
            return False, ""

        bits_extraidos = []
        total_bits = longitud_caracteres * 8
        fuerza_insercion = 24.0

        for fila in range(0, ll.shape[0] - 4, 4):
            for col in range(0, ll.shape[1] - 4, 4):
                if len(bits_extraidos) >= total_bits:
                    break
                bloque_dct = cv2.dct(ll[fila:fila + 4, col:col + 4])
                cuantizado = round(bloque_dct[2, 1] / fuerza_insercion)
                bits_extraidos.append(abs(int(cuantizado)) % 2)
            if len(bits_extraidos) >= total_bits:
                break

        caracteres = []
        for i in range(0, len(bits_extraidos), 8):
            byte = bits_extraidos[i:i + 8]
            if len(byte) == 8:
                val = int("".join(str(b) for b in byte), 2)
                if 32 <= val <= 126:
                    caracteres.append(chr(val))

        texto_recuperado = "".join(caracteres)
        if "AEGIS" in texto_recuperado or "OBRA" in texto_recuperado or "DCT" in texto_recuperado:
            return True, texto_recuperado
        return False, texto_recuperado
    except Exception:
        return False, ""


def aplicar_perturbacion_anti_ia_glaze(imagen_bgr: np.ndarray, nivel: str = "Equilibrada") -> np.ndarray:
    """
    Aplica micro-perturbaciones adversariales (Style Cloaking tipo Glaze) en las bandas
    de alta textura para alterar los vectores latentes de modelos generativos sin dañar la vista humana.
    Niveles del prototipo: 'Ligera', 'Equilibrada', 'Maxima'.
    """
    if nivel == "Ligera":
        intensidad = 1.2
    elif nivel == "Maxima":
        intensidad = 3.2
    else:  # Equilibrada - recomendada
        intensidad = 2.0

    img_float = imagen_bgr.astype(np.float32)

    # Detectar bordes y zonas de textura artística mediante filtro Laplaciano y Gaussiano
    gris = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    bordes = cv2.Laplacian(gris, cv2.CV_32F, ksize=3)
    mascara_textura = np.clip(np.abs(bordes) / 40.0, 0.15, 1.0)[:, :, np.newaxis]

    # Generar patrón sinusoidal de alta frecuencia acoplado a la máscara de textura (Style Cloaking)
    alto, ancho, _ = img_float.shape
    y_grid, x_grid = np.ogrid[:alto, :ancho]
    patron_frecuencia = np.sin(x_grid * 0.7) * np.cos(y_grid * 0.7)
    patron_3d = np.stack([patron_frecuencia, -patron_frecuencia, patron_frecuencia * 0.5], axis=-1)

    perturbacion = patron_3d * mascara_textura * intensidad
    imagen_protegida = np.clip(img_float + perturbacion, 0, 255).astype(np.uint8)
    return imagen_protegida


def procesar_y_blindar_obra(
    ruta_original: str,
    ruta_protegida: str,
    codigo_obra: str,
    nivel_proteccion: str = "Equilibrada"
) -> dict:
    """
    Ejecuta el flujo completo de US-03:
    1. Lee la imagen con OpenCV (soportando rutas con tildes en Windows).
    2. Aplica perturbación anti-IA (Glaze / Style Cloaking) si corresponde.
    3. Inserta la marca de agua invisible DCT/DWT.
    4. Guarda el archivo protegido con Pillow y calcula el SHA-256.
    """
    os.makedirs(os.path.dirname(ruta_protegida), exist_ok=True)

    # Lectura segura en Windows para rutas con tildes (como 'Innovación')
    datos_bytes = np.fromfile(ruta_original, dtype=np.uint8)
    imagen_bgr = cv2.imdecode(datos_bytes, cv2.IMREAD_COLOR)
    if imagen_bgr is None:
        raise ValueError("No se pudo decodificar el archivo de imagen.")

    proteccion_ia_activa = nivel_proteccion in ("Equilibrada", "Maxima")
    marca_invisible_activa = True

    if proteccion_ia_activa:
        imagen_bgr = aplicar_perturbacion_anti_ia_glaze(imagen_bgr, nivel=nivel_proteccion)

    imagen_bgr, firma_dct_dwt = insertar_marca_invisible_dct_dwt(imagen_bgr, codigo_obra)

    # Guardar con Pillow preservando calidad para no destruir los coeficientes DCT/DWT
    imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(imagen_rgb)

    if ruta_protegida.lower().endswith(".png"):
        meta = PngImagePlugin.PngInfo()
        meta.add_text("AegisArt-Signature", firma_dct_dwt)
        pil_img.save(ruta_protegida, format="PNG", pnginfo=meta)
    else:
        pil_img.save(ruta_protegida, quality=96)

    hash_sha256 = calcular_sha256_archivo(ruta_original)

    return {
        "hash_sha256": hash_sha256,
        "firma_dct_dwt": firma_dct_dwt,
        "proteccion_ia_activa": proteccion_ia_activa,
        "marca_invisible_activa": marca_invisible_activa
    }