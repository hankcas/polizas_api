package com.seguros.polizasapi.service;

import com.seguros.polizasapi.core.EventoCore;
import com.seguros.polizasapi.core.TipoEventoCore;
import com.seguros.polizasapi.dto.PolizaResponse;
import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.entity.Riesgo;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.EstadoRiesgo;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.exception.RecursoNoEncontradoException;
import com.seguros.polizasapi.exception.ReglaNegocioException;
import com.seguros.polizasapi.repository.PolizaRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.context.ApplicationEventPublisher;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PolizaServiceTest {

    @Mock
    private PolizaRepository polizaRepository;

    @Mock
    private ApplicationEventPublisher eventPublisher;

    @InjectMocks
    private PolizaService polizaService;

    @Test
    void renovarIncrementaCanonYPrimaSegunIpcYExtiendeVigencia() {
        Poliza poliza = poliza(TipoPoliza.COLECTIVA, EstadoPoliza.ACTIVA);
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza));

        PolizaResponse respuesta = polizaService.renovar(1L);

        assertThat(respuesta.estado()).isEqualTo(EstadoPoliza.RENOVADA);
        assertThat(respuesta.canonMensual()).isEqualByComparingTo("1052000.00");
        assertThat(respuesta.prima()).isEqualByComparingTo("105200.00");
        assertThat(respuesta.fechaInicio()).isEqualTo(LocalDate.of(2026, 1, 1));
        assertThat(respuesta.fechaFin()).isEqualTo(LocalDate.of(2027, 1, 1));

        ArgumentCaptor<EventoCore> evento = ArgumentCaptor.forClass(EventoCore.class);
        verify(eventPublisher).publishEvent(evento.capture());
        assertThat(evento.getValue().tipoEvento()).isEqualTo(TipoEventoCore.POLIZA_RENOVADA);
    }

    @Test
    void noSePuedeRenovarUnaPolizaCancelada() {
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza(TipoPoliza.INDIVIDUAL, EstadoPoliza.CANCELADA)));

        assertThatThrownBy(() -> polizaService.renovar(1L))
                .isInstanceOf(ReglaNegocioException.class)
                .hasMessageContaining("cancelada");
        verify(eventPublisher, never()).publishEvent(any(Object.class));
    }

    @Test
    void cancelarPolizaCancelaTodosSusRiesgos() {
        Poliza poliza = poliza(TipoPoliza.COLECTIVA, EstadoPoliza.ACTIVA);
        poliza.agregarRiesgo(riesgo(EstadoRiesgo.ACTIVO));
        poliza.agregarRiesgo(riesgo(EstadoRiesgo.ACTIVO));
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza));

        PolizaResponse respuesta = polizaService.cancelar(1L);

        assertThat(respuesta.estado()).isEqualTo(EstadoPoliza.CANCELADA);
        assertThat(respuesta.riesgosActivos()).isZero();
        assertThat(poliza.getRiesgos()).allMatch(r -> r.getEstado() == EstadoRiesgo.CANCELADO);
    }

    @Test
    void cancelarUnaPolizaYaCanceladaFalla() {
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza(TipoPoliza.COLECTIVA, EstadoPoliza.CANCELADA)));

        assertThatThrownBy(() -> polizaService.cancelar(1L)).isInstanceOf(ReglaNegocioException.class);
    }

    @Test
    void polizaInexistenteLanzaNoEncontrado() {
        when(polizaRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> polizaService.renovar(99L))
                .isInstanceOf(RecursoNoEncontradoException.class)
                .hasMessageContaining("99");
    }

    static Poliza poliza(TipoPoliza tipo, EstadoPoliza estado) {
        return Poliza.builder()
                .id(1L)
                .tipo(tipo)
                .estado(estado)
                .canonMensual(new BigDecimal("1000000.00"))
                .prima(new BigDecimal("100000.00"))
                .porcentajeIpc(new BigDecimal("5.20"))
                .fechaInicio(LocalDate.of(2025, 1, 1))
                .fechaFin(LocalDate.of(2026, 1, 1))
                .build();
    }

    static Riesgo riesgo(EstadoRiesgo estado) {
        return Riesgo.builder()
                .descripcion("Local")
                .direccion("Calle 1")
                .valorAsegurado(new BigDecimal("500000"))
                .estado(estado)
                .build();
    }
}
