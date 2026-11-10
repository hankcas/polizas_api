package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.dto.ErrorResponse;
import com.seguros.polizasapi.dto.PolizaResponse;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.service.PolizaService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Pólizas", description = "Consulta, renovación y cancelación de pólizas")
@ApiResponse(responseCode = "401", description = "API key ausente o inválida",
        content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
@RestController
@RequestMapping("/polizas")
@RequiredArgsConstructor
public class PolizaController {

    private final PolizaService polizaService;

    @Operation(summary = "Listar pólizas", description = "Los filtros son opcionales; sin filtros devuelve todas.")
    @ApiResponse(responseCode = "200", description = "Listado de pólizas")
    @ApiResponse(responseCode = "400", description = "Valor de filtro inválido",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @GetMapping
    public List<PolizaResponse> obtenerPolizas(
            @Parameter(description = "Tipo de póliza") @RequestParam(required = false) TipoPoliza tipo,
            @Parameter(description = "Estado de la póliza") @RequestParam(required = false) EstadoPoliza estado
    ) {
        return polizaService.obtenerPolizas(tipo, estado);
    }

    @Operation(summary = "Consultar una póliza")
    @ApiResponse(responseCode = "200", description = "Póliza encontrada")
    @ApiResponse(responseCode = "404", description = "La póliza no existe",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @GetMapping("/{id}")
    public PolizaResponse obtenerPoliza(@Parameter(description = "Id de la póliza", example = "1") @PathVariable Long id) {
        return polizaService.obtenerPoliza(id);
    }

    @Operation(summary = "Renovar una póliza",
            description = "Extiende la vigencia un año e incrementa el canon mensual y la prima según el IPC de la póliza. "
                    + "No se puede renovar una póliza cancelada.")
    @ApiResponse(responseCode = "200", description = "Póliza renovada")
    @ApiResponse(responseCode = "404", description = "La póliza no existe",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @ApiResponse(responseCode = "422", description = "La póliza está cancelada",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @PostMapping("/{id}/renovar")
    public PolizaResponse renovar(@Parameter(description = "Id de la póliza", example = "1") @PathVariable Long id) {
        return polizaService.renovar(id);
    }

    @Operation(summary = "Cancelar una póliza", description = "Cancela la póliza y todos sus riesgos.")
    @ApiResponse(responseCode = "200", description = "Póliza cancelada")
    @ApiResponse(responseCode = "404", description = "La póliza no existe",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @ApiResponse(responseCode = "422", description = "La póliza ya estaba cancelada",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @PostMapping("/{id}/cancelar")
    public PolizaResponse cancelar(@Parameter(description = "Id de la póliza", example = "2") @PathVariable Long id) {
        return polizaService.cancelar(id);
    }
}
