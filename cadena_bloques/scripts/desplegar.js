const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("1. Conectando a la blockchain local de Hardhat (http://127.0.0.1:8545)...");
  const proveedor = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
  const firmante = await proveedor.getSigner(0);

  const rutaArtefacto = path.join(
    __dirname,
    "../artefactos/contratos/RegistroAegisArt.sol/RegistroAegisArt.json"
  );
  const artefacto = JSON.parse(fs.readFileSync(rutaArtefacto, "utf8"));

  console.log("2. Desplegando el Smart Contract RegistroAegisArt...");
  const FabricaContrato = new ethers.ContractFactory(
    artefacto.abi,
    artefacto.bytecode,
    firmante
  );
  const contrato = await FabricaContrato.deploy();
  await contrato.waitForDeployment();

  const direccionContrato = await contrato.getAddress();
  console.log(`Smart Contract desplegado en la direccion: ${direccionContrato}`);

  const verificacionInicial = await contrato.verificarHash("0x0");
  console.log(`3. Contrato operativo en Hardhat EVM (verificarHash('0x0') -> ${verificacionInicial}).`);
  console.log("   Las obras reales OBRA-001..OBRA-006 se registrarán on-chain al ejecutar inicializar_bd.py.");

  const datosConexion = {
    direccion_contrato: direccionContrato,
    abi: artefacto.abi
  };

  const rutaDestinoBackend = path.join(
    __dirname,
    "../../servidor_backend/aplicacion/nucleo/datos_contrato.json"
  );

  fs.writeFileSync(rutaDestinoBackend, JSON.stringify(datosConexion, null, 2), "utf8");
  console.log("5. Archivo datos_contrato.json exportado automaticamente a FastAPI.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});