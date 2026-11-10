package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.dto.PolizaResponse;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.service.PolizaService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/polizas")
@RequiredArgsConstructor
public class PolizaController {

    private final PolizaService polizaService;

    /**
     * Lista pólizas. Los filtros {@code tipo} y {@code estado} son opcionales.
     */
    @GetMapping
    public List<PolizaResponse> obtenerPolizas(
            @RequestParam(required = false) TipoPoliza tipo,
            @RequestParam(required = false) EstadoPoliza estado
    ) {
        return polizaService.obtenerPolizas(tipo, estado);
    }

    @GetMapping("/{id}")
    public PolizaResponse obtenerPoliza(@PathVariable Long id) {
        return polizaService.obtenerPoliza(id);
    }

    @PostMapping("/{id}/renovar")
    public PolizaResponse renovar(@PathVariable Long id) {
        return polizaService.renovar(id);
    }

    @PostMapping("/{id}/cancelar")
    public PolizaResponse cancelar(@PathVariable Long id) {
        return polizaService.cancelar(id);
    }
}
