package com.seguros.polizasapi.entity;

import com.seguros.polizasapi.enums.EstadoRiesgo;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;

@Entity
@Table(name = "riesgos")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Riesgo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String descripcion;

    @Column(nullable = false)
    private String direccion;

    @Column(precision = 15, scale = 2)
    private BigDecimal valorAsegurado;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private EstadoRiesgo estado;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "poliza_id", nullable = false)
    private Poliza poliza;

    public boolean estaActivo() {
        return estado == EstadoRiesgo.ACTIVO;
    }
}
