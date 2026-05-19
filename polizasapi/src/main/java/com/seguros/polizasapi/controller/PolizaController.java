package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.service.PolizaService;

import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/polizas")
@RequiredArgsConstructor
public class PolizaController {

    private final PolizaService polizaService;

    @GetMapping
    public List<Poliza> obtenerPolizas(
            @RequestParam TipoPoliza tipo,
            @RequestParam EstadoPoliza estado
    ) {
        return polizaService.obtenerPolizas(tipo, estado);
    }

    @GetMapping("/test")
    public String test() {
        return "funciona";
    }
}