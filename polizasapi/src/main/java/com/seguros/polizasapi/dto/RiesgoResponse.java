package com.seguros.polizasapi.dto;

import com.seguros.polizasapi.entity.Riesgo;
import com.seguros.polizasapi.enums.EstadoRiesgo;

import java.math.BigDecimal;

public record RiesgoResponse(
        Long id,
        Long polizaId,
        String descripcion,
        String direccion,
        BigDecimal valorAsegurado,
        EstadoRiesgo estado
) {
    public static RiesgoResponse from(Riesgo riesgo) {
        return new RiesgoResponse(
                riesgo.getId(),
                riesgo.getPoliza().getId(),
                riesgo.getDescripcion(),
                riesgo.getDireccion(),
                riesgo.getValorAsegurado(),
                riesgo.getEstado()
        );
    }
}
