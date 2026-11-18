import os
import re
import json
import uuid
import requests
import numpy as np
import imagehash
from PIL import Image
from urllib.parse import urlparse, urljoin
from aplicacion.servicios.servicio_imagenes import (
    calcular_sha256_archivo,
    extraer_y_verificar_marca_dct_dwt
)

# Variables globales para cargar el modelo CLIP una sola vez bajo demanda
_modelo_clip = None
_procesador_clip = None
_clip_disponible = True


def _obtener_clip():
    """
    Carga perezosa (lazy loading) del modelo CLIP de Hugging Face para que el servidor
    inicie al instante y solo cargue los pesos en memoria cuando se analice una imagen.
    """
    global _modelo_clip, _procesador_clip, _clip_disponible
    if not _clip_disponible:
        return None, None
    if _modelo_clip is None:
        try:
            from transformers import CLIPProcessor, CLIPModel
            nombre_modelo = "openai/clip-vit-base-patch32"
            _procesador_clip = CLIPProcessor.from_pretrained(nombre_modelo)
            _modelo_clip = CLIPModel.from_pretrained(nombre_modelo)
            _modelo_clip.eval()
        except Exception as e:
            print(f"[Aviso CLIP] Usando vector perceptual de respaldo: {e}")
            _clip_disponible = False
            return None, None
    return _modelo_clip, _procesador_clip


def calcular_hashes_perceptuales(ruta_imagen: str) -> tuple[str, str]:
    """
    Calcula pHash y dHash usando la biblioteca ImageHash y Pillow.
    """
    with Image.open(ruta_imagen) as img:
        img_rgb = img.convert("RGB")
        phash = str(imagehash.phash(img_rgb))
        dhash = str(imagehash.dhash(img_rgb))
    return phash, dhash


def obtener_embedding_clip(ruta_imagen: str) -> list[float]:
    """
    Genera el vector numérico normalizado L2 completo (512 dims en CLIP ViT-B/32).
    Si no hay conexión/pesos locales de CLIP, genera un vector cromático espacial normalizado.
    """
    modelo, procesador = _obtener_clip()
    with Image.open(ruta_imagen) as img:
        img_rgb = img.convert("RGB")
        if modelo is not None and procesador is not None:
            import torch
            entradas = procesador(images=img_rgb, return_tensors="pt")
            with torch.no_grad():
                caracteristicas = modelo.get_image_features(**entradas)
                # En versiones recientes de transformers puede devolver un objeto o tensor
                if hasattr(caracteristicas, "pooler_output"):
                    tensor = caracteristicas.pooler_output
                elif isinstance(caracteristicas, tuple):
                    tensor = caracteristicas[0]
                else:
                    tensor = caracteristicas
                vector = tensor[0].cpu().numpy().astype(np.float32)
        else:
            # Vector de respaldo basado en redimensionado espacial normalizado
            img_peq = img_rgb.resize((16, 16))
            vector = np.array(img_peq, dtype=np.float32).flatten()

    norma = np.linalg.norm(vector)
    if norma > 0:
        vector = vector / norma
    return [round(float(x), 6) for x in vector]


def calcular_similitud_coseno_clip(vector_a: list[float] | np.ndarray, vector_b: list[float] | np.ndarray) -> float:
    """
    Calcula la similitud coseno en porcentaje [0.0, 100.0] renormalizando por seguridad.
    """
    va = np.asarray(vector_a, dtype=np.float32)
    vb = np.asarray(vector_b, dtype=np.float32)
    min_len = min(len(va), len(vb))
    if min_len == 0:
        return 0.0
    va = va[:min_len]
    vb = vb[:min_len]
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    cos_sim = float(np.dot(va, vb) / (na * nb))
    return round(max(0.0, min(100.0, cos_sim * 100.0)), 1)


def evaluar_contenido_sospechoso_us09(ruta_imagen: str, titulo: str = "") -> tuple[bool, str]:
    """
    US-09: Clasifica si una obra recién subida es 'sospechosa' (por contenido explícito
    o palabras clave de alerta) para notificar automáticamente a los moderadores activos.
    """
    palabras_alerta = ["nsfw", "explicito", "explícito", "gore", "violencia", "adulto", "sospechosa", "plagio_test"]
    texto_minuscula = titulo.lower()
    for palabra in palabras_alerta:
        if palabra in texto_minuscula:
            return True, f"Alerta automática: Título o metadato marcado como contenido sensible ({palabra})"

    modelo, procesador = _obtener_clip()
    if modelo is not None and procesador is not None:
        try:
            import torch
            with Image.open(ruta_imagen) as img:
                img_rgb = img.convert("RGB")
                etiquetas = [
                    "safe digital illustration artwork",
                    "explicit nsfw violent inappropriate content"
                ]
                entradas = procesador(text=etiquetas, images=img_rgb, return_tensors="pt", padding=True)
                with torch.no_grad():
                    salidas = modelo(**entradas)
                    probs = salidas.logits_per_image.softmax(dim=1)[0].cpu().numpy()
                    if float(probs[1]) > 0.75:
                        return True, "Detectado posible contenido explícito o sensible por visión artificial (CLIP)"
        except Exception:
            pass

    return False, ""


def comparar_similitud_obras(
    phash_original: str,
    embedding_original_json: str | None,
    ruta_imagen_candidata: str,
    phash_candidata: str | None = None,
    embedding_candidata: list[float] | None = None,
    marca_detectada_candidata: bool | None = None,
    hash_copia_candidata: str | None = None
) -> dict:
    """
    Compara una obra original contra una imagen candidata combinando:
    1. Distancia de Hamming de imageHash (pHash).
    2. Similitud coseno de los embeddings L2 completos de CLIP (512-d).
    3. Detección de marca de agua invisible DCT/DWT.
    Permite pasar huellas precalculadas de la candidata para evitar recálculos O(N).
    """
    if phash_candidata is None:
        phash_cand, _ = calcular_hashes_perceptuales(ruta_imagen_candidata)
    else:
        phash_cand = phash_candidata

    # 1. Similitud visual con imageHash (Distancia de Hamming sobre 64 bits)
    try:
        h1 = imagehash.hex_to_hash(phash_original)
        h2 = imagehash.hex_to_hash(phash_cand)
        distancia = h1 - h2
        similitud_phash = max(0.0, round((1.0 - (distancia / 64.0)) * 100.0, 1))
    except Exception:
        similitud_phash = 50.0

    # 2. Similitud semántica con CLIP (Similitud Coseno normalizada)
    similitud_clip = similitud_phash
    if embedding_original_json:
        try:
            vec_orig = json.loads(embedding_original_json)
            vec_cand = embedding_candidata if embedding_candidata is not None else obtener_embedding_clip(ruta_imagen_candidata)
            similitud_clip = calcular_similitud_coseno_clip(vec_orig, vec_cand)
        except Exception:
            similitud_clip = similitud_phash

    # 3. Verificar si la imagen candidata conserva la marca invisible DCT/DWT
    if marca_detectada_candidata is None:
        marca_detectada, _ = extraer_y_verificar_marca_dct_dwt(ruta_imagen_candidata)
    else:
        marca_detectada = marca_detectada_candidata

    # Ponderación combinada (pHash estructural + CLIP semántico)
    porcentaje_final = round((similitud_phash * 0.55) + (similitud_clip * 0.45), 1)
    if marca_detectada and porcentaje_final < 95.0:
        porcentaje_final = 98.2  # Si conserva la marca esteganográfica de AegisArt, la coincidencia es crítica

    # Determinar etiquetas de diferencias visuales detectadas
    if porcentaje_final >= 98.0:
        diferencias = "Copia exacta o ligeramente comprimida · Firma original preservada/recortada"
    elif porcentaje_final >= 85.0:
        diferencias = "Recorte de bordes · Ajuste de color · Firma original eliminada"
    else:
        diferencias = "Variación de composición · Cambio de iluminación · Compresión web"

    hash_copia = hash_copia_candidata or calcular_sha256_archivo(ruta_imagen_candidata)[:18]

    return {
        "porcentaje_similitud": porcentaje_final,
        "similitud_visual_phash": similitud_phash,
        "similitud_semantica_clip": similitud_clip,
        "marca_invisible_identificada": marca_detectada,
        "diferencias_detectadas": diferencias,
        "hash_copia_detectada": hash_copia
    }


def detectar_nombre_plataforma(url: str) -> str:
    """
    Identifica el nombre de la plataforma a partir de la URL temporal ingresada.
    """
    dominio = urlparse(url).netloc.lower()
    mapeo = {
        "instagram.com": "Instagram",
        "pinterest.com": "Pinterest",
        "behance.net": "Behance",
        "artstation.com": "ArtStation",
        "twitter.com": "X / Twitter",
        "x.com": "X / Twitter",
        "tumblr.com": "Tumblr",
        "reddit.com": "Reddit",
        "google.com": "Google Images",
    }
    for clave, nombre in mapeo.items():
        if clave in dominio:
            return nombre
    return "URL Web Externa"


def descargar_imagen_desde_url_temporal(url: str) -> str:
    """
    US-05: Recibe una URL temporal dada por el usuario en la pantalla de Monitoreo.
    - Si apunta a un archivo local del propio servidor (ej. /archivos/...), lo resuelve directamente.
    - Si es una URL directa de imagen en internet (.png, .jpg, .webp), la descarga.
    - Si es una página web HTML (como un post), busca la etiqueta <meta property="og:image"> o <img> y descarga la imagen.
    """
    carpeta_destino = "archivos_subidos/analizadas_url"
    os.makedirs(carpeta_destino, exist_ok=True)
    nombre_temp = f"url_{uuid.uuid4().hex[:10]}.png"
    ruta_destino = os.path.join(carpeta_destino, nombre_temp)

    # Caso 1: URL de prueba local apuntando a archivos subidos en nuestro servidor
    if "localhost:8000/archivos/" in url or "127.0.0.1:8000/archivos/" in url:
        ruta_relativa = url.split("/archivos/")[-1]
        ruta_local = os.path.join("archivos_subidos", ruta_relativa)
        if os.path.exists(ruta_local):
            with Image.open(ruta_local) as img:
                img.save(ruta_destino)
            return ruta_destino

    # Caso 2: Descarga HTTP/HTTPS desde internet
    cabeceras = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AegisArtBot/1.0"
    }
    respuesta = requests.get(url, headers=cabeceras, timeout=12)
    respuesta.raise_for_status()

    tipo_contenido = respuesta.headers.get("Content-Type", "").lower()

    # Si la URL devuelve un HTML en vez de una imagen directa, extraemos og:image o el primer <img>
    if "text/html" in tipo_contenido:
        html = respuesta.text
        match_og = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )
        if not match_og:
            match_og = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not match_og:
            raise ValueError("La URL proporcionada es una página web sin imágenes detectables.")
        url_imagen_extraida = urljoin(url, match_og.group(1))
        respuesta = requests.get(url_imagen_extraida, headers=cabeceras, timeout=12)
        respuesta.raise_for_status()

    with open(ruta_destino, "wb") as f:
        f.write(respuesta.content)

    # Verificar que Pillow pueda abrirla
    with Image.open(ruta_destino) as img:
        img.verify()

    return ruta_destino