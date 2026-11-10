package com.seguros.polizasapi.controller;

import com.seguros.polizasapi.core.EventoCore;
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
@Slf4j
@RestController
@RequestMapping("/core-mock/eventos")
public class CoreMockController {

    private final List<EventoCore> eventosRecibidos = new CopyOnWriteArrayList<>();

    @PostMapping
    public Map<String, String> recibirEvento(@RequestBody EventoCore evento) {
        eventosRecibidos.add(evento);
        log.info("[CORE MOCK] Evento recibido: {}", evento);
        return Map.of(
                "estado", "RECIBIDO",
                "idTransaccion", UUID.randomUUID().toString()
        );
    }

    @GetMapping
    public List<EventoCore> listarEventos() {
        return List.copyOf(eventosRecibidos);
    }
}
