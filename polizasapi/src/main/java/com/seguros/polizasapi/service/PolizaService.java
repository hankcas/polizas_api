package com.seguros.polizasapi.service;

import com.seguros.polizasapi.core.EventoCore;
import com.seguros.polizasapi.core.TipoEventoCore;
import com.seguros.polizasapi.dto.PolizaResponse;
import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.EstadoRiesgo;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.exception.RecursoNoEncontradoException;
import com.seguros.polizasapi.exception.ReglaNegocioException;
import com.seguros.polizasapi.repository.PolizaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

@Service
@RequiredArgsConstructor
public class PolizaService {

    private static final BigDecimal CIEN = BigDecimal.valueOf(100);

    private final PolizaRepository polizaRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional(readOnly = true)
    public List<PolizaResponse> obtenerPolizas(TipoPoliza tipo, EstadoPoliza estado) {
        return polizaRepository.buscar(tipo, estado).stream()
                .map(PolizaResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public PolizaResponse obtenerPoliza(Long id) {
        return PolizaResponse.from(buscarPoliza(id));
    }

    /**
     * Renueva la póliza por un año más e incrementa canon y prima según el IPC.
     * Regla: no se puede renovar una póliza cancelada.
     */
    @Transactional
    public PolizaResponse renovar(Long id) {
        Poliza poliza = buscarPoliza(id);
        if (poliza.estaCancelada()) {
            throw new ReglaNegocioException("No se puede renovar una póliza cancelada");
        }

        BigDecimal factor = BigDecimal.ONE.add(
                poliza.getPorcentajeIpc() == null ? BigDecimal.ZERO : poliza.getPorcentajeIpc().divide(CIEN));

        poliza.setCanonMensual(ajustar(poliza.getCanonMensual(), factor));
        poliza.setPrima(ajustar(poliza.getPrima(), factor));
        poliza.setFechaInicio(poliza.getFechaFin());
        poliza.setFechaFin(poliza.getFechaFin().plusYears(1));
        poliza.setEstado(EstadoPoliza.RENOVADA);

        eventPublisher.publishEvent(EventoCore.dePoliza(TipoEventoCore.POLIZA_RENOVADA, poliza.getId()));
        return PolizaResponse.from(poliza);
    }

    /**
     * Cancela la póliza y, con ella, todos sus riesgos.
     */
    @Transactional
    public PolizaResponse cancelar(Long id) {
        Poliza poliza = buscarPoliza(id);
        if (poliza.estaCancelada()) {
            throw new ReglaNegocioException("La póliza ya se encuentra cancelada");
        }

        poliza.setEstado(EstadoPoliza.CANCELADA);
        poliza.getRiesgos().forEach(r -> r.setEstado(EstadoRiesgo.CANCELADO));

        eventPublisher.publishEvent(EventoCore.dePoliza(TipoEventoCore.POLIZA_CANCELADA, poliza.getId()));
        return PolizaResponse.from(poliza);
    }

    Poliza buscarPoliza(Long id) {
        return polizaRepository.findById(id)
                .orElseThrow(() -> RecursoNoEncontradoException.poliza(id));
    }

    private static BigDecimal ajustar(BigDecimal valor, BigDecimal factor) {
        return valor == null ? null : valor.multiply(factor).setScale(2, RoundingMode.HALF_UP);
    }
}
