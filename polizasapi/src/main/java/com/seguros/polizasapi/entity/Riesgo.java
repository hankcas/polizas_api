package com.seguros.polizasapi.entity;

import com.seguros.polizasapi.enums.EstadoRiesgo;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "riesgos")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Riesgo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String descripcion;

    private String direccion;

    private Double valorAsegurado;

    @Enumerated(EnumType.STRING)
    private EstadoRiesgo estado;

    @ManyToOne
    @JoinColumn(name = "poliza_id")
    private Poliza poliza;
}