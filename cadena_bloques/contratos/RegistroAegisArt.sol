// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract RegistroAegisArt {

    struct EvidenciaObra {
        string codigoObra;
        string hashSha256;
        string nombreAutor;
        uint256 fechaRegistro;
        address cuentaRegistro;
        bool existe;
    }

    mapping(string => EvidenciaObra) private registrosPorCodigo;
    mapping(string => bool) private hashesRegistrados;
    string[] public listaCodigosObras;

    event ObraRegistrada(
        string codigoObra,
        string hashSha256,
        string nombreAutor,
        uint256 fechaRegistro,
        address cuentaRegistro
    );

    function registrarObra(
        string memory _codigoObra,
        string memory _hashSha256,
        string memory _nombreAutor
    ) public returns (uint256) {
        require(bytes(_codigoObra).length > 0, "El codigo de la obra es obligatorio");
        require(bytes(_hashSha256).length > 0, "El hash SHA-256 es obligatorio");
        require(!registrosPorCodigo[_codigoObra].existe, "Este codigo de obra ya fue registrado");
        require(!hashesRegistrados[_hashSha256], "Esta huella SHA-256 ya se encuentra registrada en la blockchain");

        uint256 tiempoActual = block.timestamp;

        registrosPorCodigo[_codigoObra] = EvidenciaObra({
            codigoObra: _codigoObra,
            hashSha256: _hashSha256,
            nombreAutor: _nombreAutor,
            fechaRegistro: tiempoActual,
            cuentaRegistro: msg.sender,
            existe: true
        });

        hashesRegistrados[_hashSha256] = true;
        listaCodigosObras.push(_codigoObra);

        emit ObraRegistrada(_codigoObra, _hashSha256, _nombreAutor, tiempoActual, msg.sender);

        return tiempoActual;
    }

    function consultarObra(string memory _codigoObra)
        public
        view
        returns (
            string memory codigoObra,
            string memory hashSha256,
            string memory nombreAutor,
            uint256 fechaRegistro,
            address cuentaRegistro
        )
    {
        require(registrosPorCodigo[_codigoObra].existe, "La obra consultada no existe en la blockchain");
        EvidenciaObra memory obra = registrosPorCodigo[_codigoObra];
        return (
            obra.codigoObra,
            obra.hashSha256,
            obra.nombreAutor,
            obra.fechaRegistro,
            obra.cuentaRegistro
        );
    }

    function verificarHash(string memory _hashSha256) public view returns (bool) {
        return hashesRegistrados[_hashSha256];
    }

    function obtenerTotalObras() public view returns (uint256) {
        return listaCodigosObras.length;
    }
}