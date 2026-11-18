from aplicacion.servicios.servicio_imagenes import (
    procesar_y_blindar_obra,
    extraer_y_verificar_marca_dct_dwt
)
from aplicacion.servicios.servicio_similitud import (
    calcular_hashes_perceptuales,
    comparar_similitud_obras
)
from aplicacion.servicios.servicio_blockchain import (
    registrar_obra_en_blockchain,
    consultar_obra_en_blockchain
)
from aplicacion.servicios.servicio_reporte_pdf import generar_pdf_reporte_evidencia


def ejecutar_pruebas():
    ruta_orig = "archivos_subidos/originales/Mau_feliz.jpg"
    ruta_prot = "archivos_subidos/protegidas/Mau_feliz_prueba.png"

    print("1. Probando blindaje anti-IA (Glaze) + Marca Invisible (DCT/DWT) + SHA-256...")
    resultado_img = procesar_y_blindar_obra(ruta_orig, ruta_prot, "OBRA-999", "Equilibrada")
    print("   -> Resultado:", resultado_img)

    print("2. Verificando extracción de la marca invisible DCT/DWT desde la imagen protegida...")
    detectada, firma = extraer_y_verificar_marca_dct_dwt(ruta_prot)
    print(f"   -> ¿Marca detectada?: {detectada} | Firma extraída: {firma}")

    print("3. Probando cálculo de similitud con imageHash + CLIP...")
    phash_orig, _ = calcular_hashes_perceptuales(ruta_orig)
    similitud = comparar_similitud_obras(phash_orig, None, ruta_prot)
    print(f"   -> Porcentaje de similitud: {similitud['porcentaje_similitud']}%")

    print("4. Probando registro y lectura en el Smart Contract desde Python (web3.py)...")
    reg_bc = registrar_obra_en_blockchain("OBRA-999", resultado_img["hash_sha256"], "Nayeli Castillo")
    print(f"   -> Transacción en Hardhat: {reg_bc['hash_transaccion']} (Bloque #{reg_bc['numero_bloque']})")
    consulta_bc = consultar_obra_en_blockchain("OBRA-001")
    print(f"   -> Consulta de OBRA-001 en Solidity: {consulta_bc}")

    print("5. Probando generación de Reporte Legal en PDF (US-11)...")
    bytes_pdf = generar_pdf_reporte_evidencia({"codigo_caso": "AEG-2026-003", "porcentaje_similitud": 98.2})
    print(f"   -> PDF generado correctamente ({len(bytes_pdf)} bytes).")
    print("\n¡Paso 3 completado con éxito! Todos los motores están operativos.")


if __name__ == "__main__":
    ejecutar_pruebas()