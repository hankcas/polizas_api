package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.core.EventoCore;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Simula el CORE transaccional. Recibe los eventos que envía {@code CoreClient}
 * y los guarda en memoria para poder consultarlos.
 */
@Tag(name = "CORE mock", description = "Simulación del CORE transaccional que recibe los eventos de la API")
@Slf4j
@RestController
@RequestMapping("/core-mock/eventos")
public class CoreMockController {

    private final List<EventoCore> eventosRecibidos = new CopyOnWriteArrayList<>();

    @Operation(summary = "Recibir un evento",
            description = "Lo invoca la propia API después de cada renovación o cancelación, y al agregar o cancelar riesgos.")
    @PostMapping
    public Map<String, String> recibirEvento(@RequestBody EventoCore evento) {
        eventosRecibidos.add(evento);
        log.info("[CORE MOCK] Evento recibido: {}", evento);
        return Map.of(
                "estado", "RECIBIDO",
                "idTransaccion", UUID.randomUUID().toString()
        );
    }

    @Operation(summary = "Listar los eventos recibidos",
            description = "Permite verificar la integración: renueva o cancela una póliza y consulta aquí el evento.")
    @GetMapping
    public List<EventoCore> listarEventos() {
        return List.copyOf(eventosRecibidos);
    }
}
