import functools
import http.server
import io
import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.principal import app
from aplicacion.nucleo.base_datos import Base, obtener_bd
from aplicacion.nucleo.seguridad import encriptar_contrasena
from aplicacion.modelos.modelos_bd import Usuario, PlanSuscripcion, Coincidencia, HuellaObra, Notificacion
from aplicacion.servicios.servicio_imagenes import (
    extraer_y_verificar_marca_dct_dwt,
    insertar_marca_invisible_dct_dwt,
)
from aplicacion.servicios.servicio_similitud import (
    calcular_hashes_perceptuales,
    obtener_embedding_clip,
    comparar_similitud_obras,
)
from ia_experimentos.entrenar_y_comparar_apf3 import generar_obra_artistica_base


def _snapshot_archivos_subidos() -> set[str]:
    presentes = set()
    if not os.path.exists("archivos_subidos"):
        return presentes
    for raiz, _, archivos in os.walk("archivos_subidos"):
        for nom in archivos:
            presentes.add(os.path.abspath(os.path.join(raiz, nom)))
    return presentes


def _img_a_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class PruebasIntegralesAegisArtAPF3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._archivos_previos = _snapshot_archivos_subidos()
        cls._tmp_dir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tmp_dir.name, "test_aegisart.db")

        cls.engine = create_engine(
            f"sqlite:///{cls._db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def _override_bd():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[obtener_bd] = _override_bd
        cls.client = TestClient(app)

        # Sembrar usuarios y planes mínimos aislados en SQLite
        db = cls.TestingSessionLocal()
        try:
            plan = PlanSuscripcion(
                nombre="Creador",
                descripcion="Plan base de prueba",
                precio=39.90,
                moneda="PEN",
                periodicidad="Mensual",
                obras_protegidas=50,
                obras_monitoreo=25,
                frecuencia_monitoreo="Diaria",
                estado="Activo",
            )
            db.add(plan)
            db.flush()

            clave = encriptar_contrasena("aegisart123")
            cls.artista = Usuario(
                nombre_apellido="Nayeli Test",
                dni="74829360",
                correo="artista.test@aegisart.pe",
                celular="+51 987 654 320",
                contrasena_hash=clave,
                especialidad="Ilustración",
                rol="artista",
                plan_id=plan.id,
            )
            cls.moderador = Usuario(
                nombre_apellido="Iris Moderadora",
                dni="75554440",
                correo="mod.test@aegisart.pe",
                celular="+51 966 555 440",
                contrasena_hash=clave,
                especialidad="Moderación",
                rol="moderador",
                plan_id=plan.id,
            )
            db.add_all([cls.artista, cls.moderador])
            db.commit()
            db.refresh(cls.artista)
            db.refresh(cls.moderador)
        finally:
            db.close()

        resp_login = cls.client.post(
            "/api/autenticacion/iniciar-sesion",
            json={"correo": "artista.test@aegisart.pe", "contrasena": "aegisart123"},
        )
        cls.token_artista = resp_login.json()["token_acceso"]
        cls.headers_artista = {"Authorization": f"Bearer {cls.token_artista}"}

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls._tmp_dir.cleanup()

        despues = _snapshot_archivos_subidos()
        for ruta in despues - cls._archivos_previos:
            try:
                os.remove(ruta)
            except OSError:
                pass

    def test_01_salud_y_metricas_ia_apf3(self):
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["estado"], "Operativo")

        r_ml = self.client.get("/api/moderacion-admin/metricas-ia-apf3")
        self.assertEqual(r_ml.status_code, 200)
        datos = r_ml.json()
        self.assertIn("Gradient Boosting", datos["algoritmo"])
        self.assertEqual(datos["total_registros_dataset"], 300)
        self.assertEqual(len(datos["comparativa_algoritmos"]), 8)
        self.assertGreaterEqual(datos["accuracy_porcentaje"], 90.0)
        self.assertGreaterEqual(datos["f1_score_porcentaje"], 90.0)

    def test_02_registro_login_y_recuperacion_segura_us01_us07(self):
        # DNI inválido rechazado con 422
        r_bad_dni = self.client.post(
            "/api/autenticacion/registro",
            json={
                "nombre_apellido": "Juan Perez",
                "dni": "123",
                "correo": "juan@example.com",
                "celular": "+51 987 654 321",
                "contrasena": "claveSegura123",
            },
        )
        self.assertEqual(r_bad_dni.status_code, 422)

        # Registro válido
        r_reg = self.client.post(
            "/api/autenticacion/registro",
            json={
                "nombre_apellido": "Juan Perez",
                "dni": "70112233",
                "correo": "juan.apf3@example.com",
                "celular": "+51 987 654 329",
                "contrasena": "claveSegura123",
            },
        )
        self.assertEqual(r_reg.status_code, 200)
        token_juan = r_reg.json()["token_acceso"]

        # Intentar restablecer SIN token debe fallar (400)
        r_no_tok = self.client.post(
            "/api/autenticacion/restablecer-contrasena",
            json={"correo": "juan.apf3@example.com", "nueva_contrasena": "nuevaClave999"},
        )
        self.assertEqual(r_no_tok.status_code, 400)

        # Solicitar token real y restablecer correctamente
        r_sol = self.client.post(
            "/api/autenticacion/recuperar-cuenta",
            json={"correo": "juan.apf3@example.com"},
        )
        self.assertEqual(r_sol.status_code, 200)
        token_rec = r_sol.json()["token_demo_prototipo"]
        self.assertTrue(token_rec.startswith("REC-"))

        r_ok = self.client.post(
            "/api/autenticacion/restablecer-contrasena",
            json={
                "correo": "juan.apf3@example.com",
                "nueva_contrasena": "nuevaClave999",
                "token_recuperacion": token_rec,
            },
        )
        self.assertEqual(r_ok.status_code, 200)

        r_login_new = self.client.post(
            "/api/autenticacion/iniciar-sesion",
            json={"correo": "juan.apf3@example.com", "contrasena": "nuevaClave999"},
        )
        self.assertEqual(r_login_new.status_code, 200)

        # Consultar y actualizar perfil autenticado
        r_perf = self.client.get(
            "/api/autenticacion/perfil",
            headers={"Authorization": f"Bearer {token_juan}"},
        )
        self.assertEqual(r_perf.status_code, 200)
        self.assertEqual(r_perf.json()["rol"], "artista")

    def test_03_validaciones_subida_obra_marca_y_clip_512d(self):
        # Formato incompatible .psd -> 400
        r_psd = self.client.post(
            "/api/obras/proteger-y-registrar",
            headers=self.headers_artista,
            data={"titulo": "Archivo PSD", "descripcion": "Test", "nivel_proteccion": "Equilibrada"},
            files={"archivo": ("boceto.psd", b"8BPS_invalid", "application/octet-stream")},
        )
        self.assertEqual(r_psd.status_code, 400)

        # Bytes corruptos con extensión .png -> 400 controlado (no 500)
        r_corrupt = self.client.post(
            "/api/obras/proteger-y-registrar",
            headers=self.headers_artista,
            data={"titulo": "Imagen corrupta", "descripcion": "Test", "nivel_proteccion": "Equilibrada"},
            files={"archivo": ("roto.png", b"no_es_png_valido", "image/png")},
        )
        self.assertEqual(r_corrupt.status_code, 400)

        # Obra legítima válida
        img_base = generar_obra_artistica_base(seed=701, tema="constelacion_nocturna", ancho=400, alto=300)
        bytes_orig = _img_a_bytes(img_base, "PNG")
        r_ok = self.client.post(
            "/api/obras/proteger-y-registrar",
            headers=self.headers_artista,
            data={"titulo": "Constelacion Original", "descripcion": "Obra legitima", "nivel_proteccion": "Equilibrada"},
            files={"archivo": ("constelacion.png", bytes_orig, "image/png")},
        )
        self.assertEqual(r_ok.status_code, 200)
        body = r_ok.json()
        self.assertFalse(body["evaluacion_ia"]["es_sospechosa"])
        self.assertEqual(body["obra"]["estado"], "Protegida")
        self.__class__.obra1_id = body["obra"]["id"]
        self.__class__.img_obra1 = img_base

        # Verificar vector CLIP completo de 512 dimensiones y marca DCT/DWT en el archivo protegido
        db = self.TestingSessionLocal()
        try:
            huella = db.query(HuellaObra).filter(HuellaObra.obra_id == self.obra1_id).first()
            vec = json.loads(huella.embedding_clip_json)
            self.assertEqual(len(vec), 512)
            ruta_prot = huella.obra.ruta_protegida
            detectada, firma = extraer_y_verificar_marca_dct_dwt(ruta_prot)
            self.assertTrue(detectada)
            self.assertIn("AEGIS", firma)

            # Verificar similitud consigo misma = 100.0%
            comp = comparar_similitud_obras(
                huella.hash_phash,
                huella.embedding_clip_json,
                huella.obra.ruta_original,
                phash_candidata=huella.hash_phash,
                embedding_candidata=vec,
                marca_detectada_candidata=False,
            )
            self.assertEqual(comp["porcentaje_similitud"], 100.0)
        finally:
            db.close()

        # Subir exactamente los mismos bytes -> rechazo por SHA-256 duplicado (400)
        r_dup = self.client.post(
            "/api/obras/proteger-y-registrar",
            headers=self.headers_artista,
            data={"titulo": "Duplicado Exacto", "descripcion": "Debe fallar", "nivel_proteccion": "Equilibrada"},
            files={"archivo": ("dup.png", bytes_orig, "image/png")},
        )
        self.assertEqual(r_dup.status_code, 400)

        # Verificar protección de imágenes muy pequeñas (10x10 px) y código largo OBRA-1234
        import cv2
        import numpy as np
        img_mini = np.zeros((10, 10, 3), dtype=np.uint8)
        _, txt_mini = insertar_marca_invisible_dct_dwt(img_mini, "OBRA-001")
        self.assertEqual(txt_mini, "AEGIS-DCT-OBRA-001")

        img_larga = np.random.randint(60, 180, (256, 256, 3), dtype=np.uint8)
        marcada, _ = insertar_marca_invisible_dct_dwt(img_larga, "OBRA-1234")
        tmp_larga = os.path.join(self._tmp_dir.name, "larga.png")
        cv2.imwrite(tmp_larga, marcada)
        ok_larga, firma_larga = extraer_y_verificar_marca_dct_dwt(tmp_larga)
        self.assertTrue(ok_larga)
        self.assertIn("OBRA-1234", firma_larga)

    def test_04_clasificacion_ml_plagio_vs_inspiracion_us08_us09(self):
        # Copia recortada 4% + leve ajuste de brillo SIN declarar US-08 -> ML debe marcar sospechosa
        w, h = self.img_obra1.size
        copia_plagio = ImageEnhance.Brightness(
            self.img_obra1.crop((int(w * 0.04), int(h * 0.04), int(w * 0.96), int(h * 0.96))).resize((w, h))
        ).enhance(1.06)

        r_plagio = self.client.post(
            "/api/obras/proteger-y-registrar",
            headers=self.headers_artista,
            data={"titulo": "Variante sin declarar", "descripcion": "Copia oculta", "nivel_proteccion": "Equilibrada"},
            files={"archivo": ("copia_oculta.png", _img_a_bytes(copia_plagio, "PNG"), "image/png")},
        )
        self.assertEqual(r_plagio.status_code, 200)
        plag_json = r_plagio.json()
        self.assertTrue(plag_json["evaluacion_ia"]["es_sospechosa"])
        self.assertEqual(plag_json["obra"]["estado"], "En revisión")
        self.__class__.obra_sosp_id = plag_json["obra"]["id"]

        # Derivada declarando inspiración (US-08) sobre obra1_id -> Gradient Boosting debe aprobarla
        derivada = ImageEnhance.Color(
            self.img_obra1.crop((int(w * 0.08), int(h * 0.08), int(w * 0.92), int(h * 0.92))).resize((w, h))
        ).enhance(1.25)
        r_deriv = self.client.post(
            "/api/obras/proteger-y-registrar",
            headers=self.headers_artista,
            data={
                "titulo": "Homenaje nocturno US-08",
                "descripcion": "Derivada declarada",
                "nivel_proteccion": "Equilibrada",
                "obra_inspirada_id": str(self.obra1_id),
            },
            files={"archivo": ("homenaje_us08.png", _img_a_bytes(derivada, "PNG"), "image/png")},
        )
        self.assertEqual(r_deriv.status_code, 200)
        self.assertFalse(r_deriv.json()["evaluacion_ia"]["es_sospechosa"])
        self.assertEqual(r_deriv.json()["obra"]["obra_inspirada_en"], "Constelacion Original")

    def test_05_monitoreo_url_filtro_24h_y_pdf_us05_us11(self):
        # Levantar servidor HTTP temporal local para probar descarga real desde URL temporal sin red externa
        carpeta_srv = os.path.join(self._tmp_dir.name, "srv")
        os.makedirs(carpeta_srv, exist_ok=True)
        copia_url = os.path.join(carpeta_srv, "repost.png")
        self.img_obra1.save(copia_url, format="PNG")

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=carpeta_srv)
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        puerto = httpd.server_address[1]
        hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
        hilo.start()

        try:
            r_scan = self.client.post(
                "/api/monitoreo/escanear-url",
                headers=self.headers_artista,
                json={"url_temporal": f"http://127.0.0.1:{puerto}/repost.png", "obra_id": self.obra1_id},
            )
            self.assertEqual(r_scan.status_code, 200)
            scan_data = r_scan.json()
            self.assertTrue(scan_data["coincidencia_detectada"])
            self.assertGreaterEqual(scan_data["porcentaje_similitud"], 95.0)
            coinc_id = scan_data["coincidencia_id"]
        finally:
            httpd.shutdown()
            httpd.server_close()

        # Insertar una coincidencia antigua (>48h) y validar que filtro 'Últimas 24 horas' la excluya
        db = self.TestingSessionLocal()
        try:
            antigua = Coincidencia(
                codigo_caso="AEG-2026-999",
                obra_original_id=self.obra1_id,
                plataforma="Pinterest",
                url_detectada="https://pinterest.com/pin/antiguo",
                ruta_imagen_copia="",
                porcentaje_similitud=88.0,
                similitud_visual_phash=88.0,
                similitud_semantica_clip=88.0,
                diferencias_detectadas="Prueba antigüedad",
                marca_invisible_identificada=False,
                hash_copia_detectada="0x1111222233334444",
                estado_artista="Pendiente",
                enviado_a_moderacion=False,
                fecha_deteccion=datetime.utcnow() - timedelta(hours=72),
            )
            db.add(antigua)
            db.commit()
        finally:
            db.close()

        r_24h = self.client.get(
            "/api/monitoreo/coincidencias?filtro=%C3%9Altimas%2024%20horas",
            headers=self.headers_artista,
        )
        self.assertEqual(r_24h.status_code, 200)
        codigos_24h = {c["codigo_caso"] for c in r_24h.json()}
        self.assertNotIn("AEG-2026-999", codigos_24h)
        self.assertGreaterEqual(len(codigos_24h), 1)

        # Enviar reclamo (apelación) y verificar descarga PDF (US-11)
        r_rec = self.client.put(
            f"/api/monitoreo/coincidencias/{coinc_id}/estado",
            json={"estado_artista": "Reclamo"},
        )
        self.assertEqual(r_rec.status_code, 200)

        r_pdf = self.client.get(f"/api/monitoreo/coincidencias/{coinc_id}/descargar-reporte-pdf")
        self.assertEqual(r_pdf.status_code, 200)
        self.assertEqual(r_pdf.headers["content-type"], "application/pdf")
        self.assertTrue(r_pdf.content.startswith(b"%PDF-"))

    def test_06_moderacion_planes_y_metricas_dueno_us06_us10_us12(self):
        # Revisar obra sospechosa desde moderación
        r_casos = self.client.get("/api/moderacion-admin/casos")
        self.assertEqual(r_casos.status_code, 200)
        ids_sosp = [o["id"] for o in r_casos.json()["obras_sospechosas"]]
        self.assertIn(self.obra_sosp_id, ids_sosp)

        r_rev = self.client.put(
            f"/api/moderacion-admin/obras-sospechosas/{self.obra_sosp_id}/revisar",
            json={"decision": "Rechazada", "comentarios": "Plagio verificado en test"},
        )
        self.assertEqual(r_rev.status_code, 200)

        # Plan inválido: monitoreo > protegidas -> 422
        r_plan_bad = self.client.post(
            "/api/planes",
            json={
                "nombre": "Plan Inválido",
                "descripcion": "Debe fallar",
                "precio": 50.0,
                "moneda": "PEN",
                "periodicidad": "Mensual",
                "obras_protegidas": 10,
                "obras_monitoreo": 20,
                "frecuencia_monitoreo": "Diaria",
                "estado": "Activo",
            },
        )
        self.assertEqual(r_plan_bad.status_code, 422)

        # Plan válido
        r_plan_ok = self.client.post(
            "/api/planes",
            json={
                "nombre": "Estudio Pro Test",
                "descripcion": "Cobertura ampliada",
                "precio": 99.90,
                "moneda": "PEN",
                "periodicidad": "Mensual",
                "obras_protegidas": 200,
                "obras_monitoreo": 150,
                "frecuencia_monitoreo": "Diaria",
                "estado": "Activo",
            },
        )
        self.assertEqual(r_plan_ok.status_code, 200)

        # Métricas globales dueño (US-12)
        r_dueno = self.client.get("/api/moderacion-admin/metricas-dueno")
        self.assertEqual(r_dueno.status_code, 200)
        m = r_dueno.json()
        self.assertGreaterEqual(m["total_artistas_registrados"], 2)
        self.assertGreaterEqual(m["total_obras_registradas"], 3)
        self.assertGreaterEqual(m["total_certificados_blockchain"], 3)


if __name__ == "__main__":
    unittest.main()
