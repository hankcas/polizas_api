package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.dto.ErrorResponse;
import com.seguros.polizasapi.dto.RiesgoRequest;
import com.seguros.polizasapi.dto.RiesgoResponse;
import com.seguros.polizasapi.service.RiesgoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.util.List;

@Tag(name = "Riesgos", description = "Consulta, alta y cancelación de los riesgos de una póliza")
@ApiResponse(responseCode = "401", description = "API key ausente o inválida",
        content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
@RestController
@RequiredArgsConstructor
public class RiesgoController {

    private final RiesgoService riesgoService;

    @Operation(summary = "Listar los riesgos de una póliza")
    @ApiResponse(responseCode = "200", description = "Riesgos de la póliza")
    @ApiResponse(responseCode = "404", description = "La póliza no existe",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @GetMapping("/polizas/{polizaId}/riesgos")
    public List<RiesgoResponse> obtenerRiesgos(
            @Parameter(description = "Id de la póliza", example = "2") @PathVariable Long polizaId) {
        return riesgoService.obtenerRiesgos(polizaId);
    }

    @Operation(summary = "Agregar un riesgo a una póliza",
            description = "Solo las pólizas colectivas que no estén canceladas permiten agregar riesgos.")
    @ApiResponse(responseCode = "201", description = "Riesgo creado")
    @ApiResponse(responseCode = "400", description = "Campos inválidos",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @ApiResponse(responseCode = "404", description = "La póliza no existe",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @ApiResponse(responseCode = "422", description = "La póliza es individual o está cancelada",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @PostMapping("/polizas/{polizaId}/riesgos")
    public ResponseEntity<RiesgoResponse> agregarRiesgo(
            @Parameter(description = "Id de la póliza", example = "2") @PathVariable Long polizaId,
            @Valid @RequestBody RiesgoRequest request
    ) {
        RiesgoResponse creado = riesgoService.agregarRiesgo(polizaId, request);
        URI location = ServletUriComponentsBuilder.fromCurrentContextPath()
                .path("/riesgos/{id}")
                .buildAndExpand(creado.id())
                .toUri();
        return ResponseEntity.created(location).body(creado);
    }

    @Operation(summary = "Cancelar un riesgo")
    @ApiResponse(responseCode = "200", description = "Riesgo cancelado")
    @ApiResponse(responseCode = "404", description = "El riesgo no existe",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @ApiResponse(responseCode = "422", description = "El riesgo ya estaba cancelado",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class)))
    @PostMapping("/riesgos/{id}/cancelar")
    public RiesgoResponse cancelarRiesgo(
            @Parameter(description = "Id del riesgo", example = "3") @PathVariable Long id) {
        return riesgoService.cancelarRiesgo(id);
    }
}
