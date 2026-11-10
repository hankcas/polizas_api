package com.seguros.polizasapi.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

@Schema(description = "Datos para agregar un riesgo a una póliza colectiva")
public record RiesgoRequest(
        @Schema(description = "Descripción del bien asegurado", example = "Bodega sur")
        @NotBlank(message = "La descripción es obligatoria")
        @Size(max = 255, message = "La descripción no puede superar 255 caracteres")
        String descripcion,

        @Schema(description = "Dirección del bien asegurado", example = "Calle 13 # 68-90, Bogotá")
        @NotBlank(message = "La dirección es obligatoria")
        @Size(max = 255, message = "La dirección no puede superar 255 caracteres")
        String direccion,

        @Schema(description = "Valor asegurado en pesos", example = "1800000")
        @NotNull(message = "El valor asegurado es obligatorio")
        @Positive(message = "El valor asegurado debe ser mayor a cero")
        BigDecimal valorAsegurado
) {
}
