package com.seguros.polizasapi.service;

import com.seguros.polizasapi.core.EventoCore;
import com.seguros.polizasapi.core.TipoEventoCore;
import com.seguros.polizasapi.dto.RiesgoRequest;
import com.seguros.polizasapi.dto.RiesgoResponse;
import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.entity.Riesgo;
import com.seguros.polizasapi.enums.EstadoRiesgo;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.exception.RecursoNoEncontradoException;
import com.seguros.polizasapi.exception.ReglaNegocioException;
import com.seguros.polizasapi.repository.PolizaRepository;
import com.seguros.polizasapi.repository.RiesgoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class RiesgoService {

    private final PolizaRepository polizaRepository;
    private final RiesgoRepository riesgoRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Transactional(readOnly = true)
    public List<RiesgoResponse> obtenerRiesgos(Long polizaId) {
        if (!polizaRepository.existsById(polizaId)) {
            throw RecursoNoEncontradoException.poliza(polizaId);
        }
        return riesgoRepository.findByPolizaIdOrderByIdAsc(polizaId).stream()
                .map(RiesgoResponse::from)
                .toList();
    }

    /**
     * Agrega un riesgo a la póliza.
     * Reglas: solo las pólizas colectivas permiten agregar riesgos (una individual tiene
     * un único riesgo) y no se agregan riesgos a pólizas canceladas.
     */
    @Transactional
    public RiesgoResponse agregarRiesgo(Long polizaId, RiesgoRequest request) {
        Poliza poliza = polizaRepository.findById(polizaId)
                .orElseThrow(() -> RecursoNoEncontradoException.poliza(polizaId));

        if (poliza.estaCancelada()) {
            throw new ReglaNegocioException("No se pueden agregar riesgos a una póliza cancelada");
        }
        if (poliza.getTipo() == TipoPoliza.INDIVIDUAL) {
            throw new ReglaNegocioException(
                    "Solo las pólizas colectivas permiten agregar riesgos; una póliza individual tiene un único riesgo");
        }

        Riesgo riesgo = Riesgo.builder()
                .descripcion(request.descripcion().trim())
                .direccion(request.direccion().trim())
                .valorAsegurado(request.valorAsegurado())
                .estado(EstadoRiesgo.ACTIVO)
                .build();
        poliza.agregarRiesgo(riesgo);
        riesgo = riesgoRepository.save(riesgo);

        eventPublisher.publishEvent(EventoCore.deRiesgo(TipoEventoCore.RIESGO_AGREGADO, polizaId, riesgo.getId()));
        return RiesgoResponse.from(riesgo);
    }

    @Transactional
    public RiesgoResponse cancelarRiesgo(Long riesgoId) {
        Riesgo riesgo = riesgoRepository.findById(riesgoId)
                .orElseThrow(() -> RecursoNoEncontradoException.riesgo(riesgoId));

        if (!riesgo.estaActivo()) {
            throw new ReglaNegocioException("El riesgo ya se encuentra cancelado");
        }

        riesgo.setEstado(EstadoRiesgo.CANCELADO);

        eventPublisher.publishEvent(EventoCore.deRiesgo(
                TipoEventoCore.RIESGO_CANCELADO, riesgo.getPoliza().getId(), riesgo.getId()));
        return RiesgoResponse.from(riesgo);
    }
}
