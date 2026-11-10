package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.dto.RiesgoRequest;
import com.seguros.polizasapi.dto.RiesgoResponse;
import com.seguros.polizasapi.service.RiesgoService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.util.List;

@RestController
@RequiredArgsConstructor
public class RiesgoController {

    private final RiesgoService riesgoService;

    @GetMapping("/polizas/{polizaId}/riesgos")
    public List<RiesgoResponse> obtenerRiesgos(@PathVariable Long polizaId) {
        return riesgoService.obtenerRiesgos(polizaId);
    }

    @PostMapping("/polizas/{polizaId}/riesgos")
    public ResponseEntity<RiesgoResponse> agregarRiesgo(
            @PathVariable Long polizaId,
            @Valid @RequestBody RiesgoRequest request
    ) {
        RiesgoResponse creado = riesgoService.agregarRiesgo(polizaId, request);
        URI location = ServletUriComponentsBuilder.fromCurrentContextPath()
                .path("/riesgos/{id}")
                .buildAndExpand(creado.id())
                .toUri();
        return ResponseEntity.created(location).body(creado);
    }

    @PostMapping("/riesgos/{id}/cancelar")
    public RiesgoResponse cancelarRiesgo(@PathVariable Long id) {
        return riesgoService.cancelarRiesgo(id);
    }
}
