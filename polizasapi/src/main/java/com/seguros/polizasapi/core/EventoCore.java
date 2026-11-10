package com.seguros.polizasapi.core;

import java.time.LocalDateTime;

/**
 * Evento que se notifica al CORE transaccional cuando cambia una póliza o un riesgo.
 */
public record EventoCore(
        TipoEventoCore tipoEvento,
        Long polizaId,
        Long riesgoId,
        LocalDateTime fecha
) {
    public static EventoCore dePoliza(TipoEventoCore tipo, Long polizaId) {
        return new EventoCore(tipo, polizaId, null, LocalDateTime.now());
    }

    public static EventoCore deRiesgo(TipoEventoCore tipo, Long polizaId, Long riesgoId) {
        return new EventoCore(tipo, polizaId, riesgoId, LocalDateTime.now());
    }
}
