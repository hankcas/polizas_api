package com.seguros.polizasapi.service;

import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;
import com.seguros.polizasapi.repository.PolizaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PolizaService {

    private final PolizaRepository polizaRepository;

    public List<Poliza> obtenerPolizas(TipoPoliza tipo, EstadoPoliza estado) {
        return polizaRepository.findByTipoAndEstado(tipo, estado);
    }
}