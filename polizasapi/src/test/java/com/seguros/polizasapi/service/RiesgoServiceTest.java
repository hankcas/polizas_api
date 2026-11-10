package com.seguros.polizasapi.service;

import com.seguros.polizasapi.dto.RiesgoRequest;
import com.seguros.polizasapi.dto.RiesgoResponse;
import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.entity.Riesgo;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.EstadoRiesgo;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.exception.RecursoNoEncontradoException;
import com.seguros.polizasapi.exception.ReglaNegocioException;
import com.seguros.polizasapi.repository.PolizaRepository;
import com.seguros.polizasapi.repository.RiesgoRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.context.ApplicationEventPublisher;

import java.math.BigDecimal;
import java.util.Optional;

import static com.seguros.polizasapi.service.PolizaServiceTest.poliza;
import static com.seguros.polizasapi.service.PolizaServiceTest.riesgo;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RiesgoServiceTest {

    private static final RiesgoRequest REQUEST =
            new RiesgoRequest("Bodega", "Calle 10 # 5-20", new BigDecimal("2000000"));

    @Mock
    private PolizaRepository polizaRepository;

    @Mock
    private RiesgoRepository riesgoRepository;

    @Mock
    private ApplicationEventPublisher eventPublisher;

    @InjectMocks
    private RiesgoService riesgoService;

    @Test
    void agregarRiesgoAPolizaColectiva() {
        Poliza poliza = poliza(TipoPoliza.COLECTIVA, EstadoPoliza.ACTIVA);
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza));
        when(riesgoRepository.save(any(Riesgo.class))).thenAnswer(inv -> {
            Riesgo r = inv.getArgument(0);
            r.setId(10L);
            return r;
        });

        RiesgoResponse respuesta = riesgoService.agregarRiesgo(1L, REQUEST);

        assertThat(respuesta.id()).isEqualTo(10L);
        assertThat(respuesta.polizaId()).isEqualTo(1L);
        assertThat(respuesta.estado()).isEqualTo(EstadoRiesgo.ACTIVO);
        assertThat(poliza.getRiesgos()).hasSize(1);
        verify(eventPublisher).publishEvent(any(Object.class));
    }

    @Test
    void polizaIndividualNoPermiteAgregarRiesgos() {
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza(TipoPoliza.INDIVIDUAL, EstadoPoliza.ACTIVA)));

        assertThatThrownBy(() -> riesgoService.agregarRiesgo(1L, REQUEST))
                .isInstanceOf(ReglaNegocioException.class)
                .hasMessageContaining("colectivas");
        verify(riesgoRepository, never()).save(any());
    }

    @Test
    void polizaCanceladaNoPermiteAgregarRiesgos() {
        when(polizaRepository.findById(1L)).thenReturn(Optional.of(poliza(TipoPoliza.COLECTIVA, EstadoPoliza.CANCELADA)));

        assertThatThrownBy(() -> riesgoService.agregarRiesgo(1L, REQUEST))
                .isInstanceOf(ReglaNegocioException.class)
                .hasMessageContaining("cancelada");
    }

    @Test
    void cancelarRiesgoActivo() {
        Poliza poliza = poliza(TipoPoliza.COLECTIVA, EstadoPoliza.ACTIVA);
        Riesgo riesgo = riesgo(EstadoRiesgo.ACTIVO);
        riesgo.setId(5L);
        poliza.agregarRiesgo(riesgo);
        when(riesgoRepository.findById(5L)).thenReturn(Optional.of(riesgo));

        RiesgoResponse respuesta = riesgoService.cancelarRiesgo(5L);

        assertThat(respuesta.estado()).isEqualTo(EstadoRiesgo.CANCELADO);
    }

    @Test
    void cancelarRiesgoYaCanceladoFalla() {
        Riesgo riesgo = riesgo(EstadoRiesgo.CANCELADO);
        when(riesgoRepository.findById(5L)).thenReturn(Optional.of(riesgo));

        assertThatThrownBy(() -> riesgoService.cancelarRiesgo(5L)).isInstanceOf(ReglaNegocioException.class);
    }

    @Test
    void obtenerRiesgosDePolizaInexistenteFalla() {
        when(polizaRepository.existsById(99L)).thenReturn(false);

        assertThatThrownBy(() -> riesgoService.obtenerRiesgos(99L)).isInstanceOf(RecursoNoEncontradoException.class);
    }
}
