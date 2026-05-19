package com.seguros.polizasapi.entity;

import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.List;

@Entity
@Table(name = "polizas")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Poliza {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    private TipoPoliza tipo;

    @Enumerated(EnumType.STRING)
    private EstadoPoliza estado;

    private Double canonMensual;

    private Double prima;

    private Double porcentajeIpc;

    private LocalDate fechaInicio;

    private LocalDate fechaFin;

    @OneToMany(mappedBy = "poliza", cascade = CascadeType.ALL)
    private List<Riesgo> riesgos;
}