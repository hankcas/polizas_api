package com.seguros.polizasapi.dto;

import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.entity.Riesgo;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PolizaResponse(
        Long id,
        TipoPoliza tipo,
        EstadoPoliza estado,
        BigDecimal canonMensual,
        BigDecimal prima,
        BigDecimal porcentajeIpc,
        LocalDate fechaInicio,
        LocalDate fechaFin,
        long riesgosActivos
) {
    public static PolizaResponse from(Poliza poliza) {
        long activos = poliza.getRiesgos().stream().filter(Riesgo::estaActivo).count();
        return new PolizaResponse(
                poliza.getId(),
                poliza.getTipo(),
                poliza.getEstado(),
                poliza.getCanonMensual(),
                poliza.getPrima(),
                poliza.getPorcentajeIpc(),
                poliza.getFechaInicio(),
                poliza.getFechaFin(),
                activos
        );
    }
}
