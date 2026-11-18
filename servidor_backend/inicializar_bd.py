import os
import json
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
from aplicacion.nucleo.base_datos import motor_bd, SesionLocal, Base
from aplicacion.nucleo.seguridad import encriptar_contrasena, verificar_contrasena
from aplicacion.servicios.servicio_nube_r2 import subir_obra_a_cloudflare_r2
from aplicacion.servicios.servicio_ia_apf3 import (
    generar_y_entrenar_modelo_apf3,
    predecir_obra_sospechosa_ml,
)
from aplicacion.servicios.servicio_imagenes import (
    procesar_y_blindar_obra,
    extraer_y_verificar_marca_dct_dwt,
)
from aplicacion.servicios.servicio_similitud import (
    calcular_hashes_perceptuales,
    obtener_embedding_clip,
    comparar_similitud_obras,
)
from aplicacion.servicios.servicio_blockchain import registrar_obra_en_blockchain
from ia_experimentos.entrenar_y_comparar_apf3 import generar_obra_artistica_base
from aplicacion.modelos.modelos_bd import (
    PlanSuscripcion, Usuario, Obra, HuellaObra,
    RegistroBlockchain, EscaneoUrl, Coincidencia, Notificacion
)


def crear_imagen_demo(ruta: str, seed: int, tema: str, variante_copia_de: str | None = None):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    if variante_copia_de and os.path.exists(variante_copia_de):
        # Genera una copia real modificada (recorte sutil + ajuste de brillo) sobre una obra previa
        with Image.open(variante_copia_de) as base_img:
            img = base_img.convert("RGB")
            w, h = img.size
            recorte = img.crop((int(w * 0.04), int(h * 0.04), int(w * 0.96), int(h * 0.96))).resize((w, h), Image.Resampling.LANCZOS)
            img = ImageEnhance.Brightness(recorte).enhance(1.06)
    else:
        img = generar_obra_artistica_base(seed=seed, tema=tema, ancho=640, alto=480)

    if ruta.lower().endswith(".jpg") or ruta.lower().endswith(".jpeg"):
        img.save(ruta, format="JPEG", quality=94)
    else:
        img.save(ruta, format="PNG")


def inicializar_datos():
    print("1. Reiniciando y creando tablas limpias en PostgreSQL...")
    Base.metadata.drop_all(bind=motor_bd)
    Base.metadata.create_all(bind=motor_bd)

    print("2. Entrenando modelo de Machine Learning Supervisado (Gradient Boosting - APF3 Ruta A)...")
    metricas = generar_y_entrenar_modelo_apf3()
    print(
        f"   -> Modelo entrenado: {metricas['algoritmo']} | "
        f"Accuracy Test: {metricas['accuracy_porcentaje']}% | F1 Test: {metricas['f1_score_porcentaje']}% | "
        f"CV F1: {metricas.get('cv_f1_entrenamiento_porcentaje', 'N/A')}%"
    )

    bd = SesionLocal()
    try:
        print("3. Insertando los 4 planes de suscripción del prototipo (US-06)...")
        planes = [
            PlanSuscripcion(
                nombre="Junior",
                descripcion="Protección para un catálogo en crecimiento.",
                precio=0.00, moneda="PEN", periodicidad="Semanal",
                obras_protegidas=50, obras_monitoreo=10, frecuencia_monitoreo="Semanal", estado="Activo"
            ),
            PlanSuscripcion(
                nombre="Inicial",
                descripcion="Cobertura básica para tus primeras obras.",
                precio=19.90, moneda="PEN", periodicidad="Mensual",
                obras_protegidas=100, obras_monitoreo=100, frecuencia_monitoreo="Semanal", estado="Inactivo"
            ),
            PlanSuscripcion(
                nombre="Creador",
                descripcion="Protección y monitoreo para hasta 50 obras.",
                precio=39.90, moneda="PEN", periodicidad="Mensual",
                obras_protegidas=50, obras_monitoreo=25, frecuencia_monitoreo="Diaria", estado="Activo"
            ),
            PlanSuscripcion(
                nombre="Profesional",
                descripcion="Más cobertura para tu portafolio creativo.",
                precio=79.90, moneda="PEN", periodicidad="Mensual",
                obras_protegidas=300, obras_monitoreo=300, frecuencia_monitoreo="Diaria", estado="Activo"
            ),
        ]
        bd.add_all(planes)
        bd.commit()

        plan_creador = bd.query(PlanSuscripcion).filter_by(nombre="Creador").first()

        print("4. Creando y verificando las cuentas por Rol (Artista, Moderador y Dueña)...")
        hash_clave = encriptar_contrasena("aegisart123")
        assert verificar_contrasena("aegisart123", hash_clave), "Error en verificación de bcrypt"

        nayeli = Usuario(
            nombre_apellido="Nayeli Castillo",
            dni="74829361",
            correo="nayelis@gmail.com",
            celular="+51 987 654 321",
            contrasena_hash=hash_clave,
            especialidad="Artista digital",
            rol="artista",
            plan_id=plan_creador.id
        )
        valentina = Usuario(
            nombre_apellido="Valentina Torres",
            dni="71234567",
            correo="valentina@example.com",
            celular="+51 912 345 678",
            contrasena_hash=hash_clave,
            especialidad="Artista digital",
            rol="artista",
            plan_id=plan_creador.id
        )
        moderador = Usuario(
            nombre_apellido="Iris Arroyo (Moderadora)",
            dni="75554443",
            correo="moderador@aegisart.pe",
            celular="+51 966 555 444",
            contrasena_hash=hash_clave,
            especialidad="Moderación de Contenido y Propiedad Intelectual",
            rol="moderador",
            plan_id=plan_creador.id
        )
        noemi_duena = Usuario(
            nombre_apellido="Noemi Cusquisiban",
            dni="70987654",
            correo="admin@aegisart.pe",
            celular="+51 999 888 777",
            contrasena_hash=hash_clave,
            especialidad="Dueña de Producto · Administración",
            rol="dueno",
            plan_id=plan_creador.id
        )
        bd.add_all([nayeli, valentina, moderador, noemi_duena])
        bd.commit()

        print("5. Creando obras reales, blindando DCT/DWT + Glaze, subiendo a Cloudflare R2 y calculando CLIP 512-d...")
        obras_semilla = [
            {
                "codigo": "OBRA-001", "titulo": "Ecos de otro mundo",
                "descripcion": "Ilustración conceptual en tonos pastel.",
                "archivo": "ecos_de_otro_mundo.png", "seed": 101, "tema": "pastel_minimalista",
                "estado": "Coincidencia encontrada", "certificado": "AEG-2026-0024",
                "autor": nayeli, "copia_de_orig": None
            },
            {
                "codigo": "OBRA-002", "titulo": "Jardín de lo imposible",
                "descripcion": "Criatura nocturna alcanzando una constelación luminosa.",
                "archivo": "jardin_imposible.png", "seed": 202, "tema": "constelacion_nocturna",
                "estado": "Coincidencia encontrada", "certificado": "AEG-2026-0025",
                "autor": nayeli, "copia_de_orig": None
            },
            {
                "codigo": "OBRA-003", "titulo": "Entre dimensiones",
                "descripcion": "Composición geométrica luminosa de planos superpuestos.",
                "archivo": "entre_dimensiones.png", "seed": 303, "tema": "geometrico_bauhaus",
                "estado": "Monitoreando", "certificado": "AEG-2026-0026",
                "autor": nayeli, "copia_de_orig": None
            },
            {
                "codigo": "OBRA-004", "titulo": "Horizonte carmesí",
                "descripcion": "Retrato artístico en tonos cálidos y contrastes violeta.",
                "archivo": "horizonte_carmesi.png", "seed": 404, "tema": "retrato_calido",
                "estado": "Protegida", "certificado": "AEG-2026-0027",
                "autor": nayeli, "copia_de_orig": None
            },
            {
                "codigo": "OBRA-005", "titulo": "Mau Feliz",
                "descripcion": "Un retrato a tinta de trazos expresivos y finos contrastes.",
                "archivo": "Mau_feliz.jpg", "seed": 505, "tema": "arte_lineal",
                "estado": "Protegida", "certificado": "AEG-2026-0028",
                "autor": nayeli, "copia_de_orig": None
            },
            {
                "codigo": "OBRA-006", "titulo": "Boceto derivado sin declarar",
                "descripcion": "Variante visual subida sin declarar obra de referencia para validación real ML (US-09/US-10).",
                "archivo": "boceto_sospechoso.png", "seed": 606, "tema": "pastel_minimalista",
                "estado": "En revisión", "certificado": "AEG-2026-0029",
                "autor": valentina, "copia_de_orig": "archivos_subidos/originales/ecos_de_otro_mundo.png"
            }
        ]

        obras_creadas = []
        huellas_creadas = []
        ahora = datetime.utcnow()
        for idx, item in enumerate(obras_semilla):
            ruta_orig = f"archivos_subidos/originales/{item['archivo']}"
            ruta_prot = f"archivos_subidos/protegidas/{item['archivo']}"
            crear_imagen_demo(ruta_orig, item["seed"], item["tema"], variante_copia_de=item["copia_de_orig"])
            tamano_mb = round(max(os.path.getsize(ruta_orig) / (1024 * 1024), 0.05), 2)

            datos_blindaje = procesar_y_blindar_obra(
                ruta_original=ruta_orig,
                ruta_protegida=ruta_prot,
                codigo_obra=item["codigo"],
                nivel_proteccion="Equilibrada"
            )
            subir_obra_a_cloudflare_r2(ruta_prot, item["archivo"])

            phash, dhash = calcular_hashes_perceptuales(ruta_orig)
            vector_clip = obtener_embedding_clip(ruta_orig)
            marca_ajena, _ = extraer_y_verificar_marca_dct_dwt(ruta_orig)

            # Comparar contra el catálogo previo real y evaluar con Gradient Boosting (US-09)
            mayor_sim = 0.0
            mejor_phash = 0.0
            mejor_clip = 0.0
            mejor_criterio = (-1.0, -1.0)
            for h_prev in huellas_creadas:
                comp = comparar_similitud_obras(
                    phash_original=h_prev.hash_phash,
                    embedding_original_json=h_prev.embedding_clip_json,
                    ruta_imagen_candidata=ruta_orig,
                    phash_candidata=phash,
                    embedding_candidata=vector_clip,
                    marca_detectada_candidata=marca_ajena,
                    hash_copia_candidata=datos_blindaje["hash_sha256"][:18],
                )
                crit = (comp["porcentaje_similitud"], comp["similitud_visual_phash"] * 0.55 + comp["similitud_semantica_clip"] * 0.45)
                if crit > mejor_criterio:
                    mejor_criterio = crit
                    mayor_sim = comp["porcentaje_similitud"]
                    mejor_phash = comp["similitud_visual_phash"]
                    mejor_clip = comp["similitud_semantica_clip"]

            resultado_ml = predecir_obra_sospechosa_ml(
                ruta_imagen=ruta_orig,
                titulo=item["titulo"],
                similitud_maxima=mayor_sim,
                declarada_inspirada=False,
                similitud_phash=mejor_phash,
                similitud_clip=mejor_clip,
                marca_ajena_detectada=marca_ajena,
            )
            es_sospechosa = resultado_ml["es_sospechosa"]
            estado_obra = "En revisión" if es_sospechosa else item["estado"]

            obra = Obra(
                codigo_obra=item["codigo"],
                titulo=item["titulo"],
                descripcion=item["descripcion"],
                nombre_archivo=item["archivo"],
                formato="PNG" if item["archivo"].endswith(".png") else "JPG",
                tamano_mb=tamano_mb,
                ruta_original=ruta_orig,
                ruta_protegida=ruta_prot,
                nivel_proteccion="Equilibrada",
                proteccion_ia_activa=datos_blindaje["proteccion_ia_activa"],
                marca_invisible_activa=datos_blindaje["marca_invisible_activa"],
                estado=estado_obra,
                es_sospechosa=es_sospechosa,
                motivo_sospecha=resultado_ml["motivo_sospecha"] if es_sospechosa else None,
                estado_moderacion="Pendiente" if es_sospechosa else "Aprobada",
                autor_id=item["autor"].id,
                fecha_registro=ahora - timedelta(days=max(1, 6 - idx))
            )
            bd.add(obra)
            bd.flush()

            huella = HuellaObra(
                obra_id=obra.id,
                hash_sha256=datos_blindaje["hash_sha256"],
                hash_phash=phash,
                hash_dhash=dhash,
                firma_dct_dwt=datos_blindaje["firma_dct_dwt"],
                embedding_clip_json=json.dumps(vector_clip)
            )
            bd.add(huella)
            huellas_creadas.append(huella)

            datos_bc = registrar_obra_en_blockchain(
                codigo_obra=item["codigo"],
                hash_sha256=datos_blindaje["hash_sha256"],
                nombre_autor=item["autor"].nombre_apellido
            )
            bd.add(RegistroBlockchain(
                codigo_certificado=item["certificado"],
                obra_id=obra.id,
                hash_sha256_registrado=datos_blindaje["hash_sha256"],
                hash_transaccion=datos_bc["hash_transaccion"],
                direccion_contrato=datos_bc["direccion_contrato"],
                numero_bloque=datos_bc["numero_bloque"],
                red_blockchain=datos_bc["red_blockchain"]
            ))
            obras_creadas.append(obra)

        bd.commit()

        print("6. Insertando coincidencias reales y notificaciones (US-05, US-09, US-10)...")
        bd.add_all([
            Coincidencia(
                codigo_caso="AEG-2026-003",
                obra_original_id=obras_creadas[0].id,
                plataforma="Instagram",
                url_detectada="https://instagram.com/p/repost_no_autorizado_1",
                ruta_imagen_copia=obras_creadas[0].ruta_protegida,
                porcentaje_similitud=98.2,
                similitud_visual_phash=98.0,
                similitud_semantica_clip=98.4,
                diferencias_detectadas="Recorte de bordes · Ajuste de color · Marca DCT/DWT preservada",
                marca_invisible_identificada=True,
                hash_copia_detectada=huellas_creadas[0].hash_sha256[:18],
                estado_artista="Pendiente",
                enviado_a_moderacion=True,
                motivo_reporte="Uso sin autorización",
                estado_moderador="En revisión",
                fecha_deteccion=ahora - timedelta(hours=6)
            ),
            Coincidencia(
                codigo_caso="AEG-2026-004",
                obra_original_id=obras_creadas[1].id,
                plataforma="Instagram",
                url_detectada="https://instagram.com/p/repost_no_autorizado_2",
                ruta_imagen_copia=obras_creadas[1].ruta_protegida,
                porcentaje_similitud=94.0,
                similitud_visual_phash=93.5,
                similitud_semantica_clip=94.5,
                diferencias_detectadas="Recorte de bordes · Ajuste de color · Firma original eliminada",
                marca_invisible_identificada=True,
                hash_copia_detectada=huellas_creadas[1].hash_sha256[:18],
                estado_artista="Confirmado",
                enviado_a_moderacion=False,
                fecha_deteccion=ahora - timedelta(hours=18)
            ),
            Coincidencia(
                codigo_caso="AEG-2026-005",
                obra_original_id=obras_creadas[2].id,
                plataforma="Pinterest",
                url_detectada="https://pinterest.com/pin/8823192",
                ruta_imagen_copia=obras_creadas[2].ruta_protegida,
                porcentaje_similitud=82.0,
                similitud_visual_phash=80.0,
                similitud_semantica_clip=84.0,
                diferencias_detectadas="Cambio de iluminación · Compresión web",
                marca_invisible_identificada=False,
                hash_copia_detectada=huellas_creadas[2].hash_sha256[:18],
                estado_artista="Descartado",
                enviado_a_moderacion=False,
                fecha_deteccion=ahora - timedelta(days=3)
            )
        ])

        obra_sosp = obras_creadas[5]
        notificaciones_semilla = [
            Notificacion(
                usuario_destino_id=nayeli.id, rol_destino="artista",
                titulo="2 nuevas coincidencias",
                mensaje="Se detectaron imágenes muy parecidas a tus obras.",
                tipo="coincidencia", referencia_codigo="AEG-2026-003"
            ),
            Notificacion(
                usuario_destino_id=moderador.id, rol_destino="moderador",
                titulo="Apelación enviada a revisión: AEG-003",
                mensaje="Revisión de similitud (98.2%) y marca invisible detectada.",
                tipo="sospechosa", referencia_codigo="AEG-2026-003"
            )
        ]
        if obra_sosp.es_sospechosa:
            notificaciones_semilla.append(
                Notificacion(
                    usuario_destino_id=moderador.id, rol_destino="moderador",
                    titulo=f"Alerta ML (US-09): Obra sospechosa {obra_sosp.codigo_obra}",
                    mensaje=obra_sosp.motivo_sospecha or "Obra enviada a moderación por similitud alta sin declarar.",
                    tipo="sospechosa", referencia_codigo=obra_sosp.codigo_obra
                )
            )
        bd.add_all(notificaciones_semilla)
        bd.commit()

        print("\n========================================================")
        print("✅ ¡BASE DE DATOS, CLOUDFLARE R2 Y MODELO IA LISTOS!")
        print("   • Artista   -> Correo: nayelis@gmail.com     | Clave: aegisart123")
        print("   • Moderador -> Correo: moderador@aegisart.pe | Clave: aegisart123")
        print("   • Dueña     -> Correo: admin@aegisart.pe     | Clave: aegisart123")
        print("========================================================\n")
    finally:
        bd.close()


if __name__ == "__main__":
    inicializar_datos()