package com.seguros.polizasapi.repository;

import com.seguros.polizasapi.entity.Poliza;
import com.seguros.polizasapi.enums.EstadoPoliza;
import com.seguros.polizasapi.enums.TipoPoliza;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface PolizaRepository extends JpaRepository<Poliza, Long> {

    /**
     * Busca pólizas filtrando opcionalmente por tipo y estado (un filtro nulo no se aplica).
     */
    @Query("""
            select distinct p from Poliza p
            left join fetch p.riesgos
            where (:tipo is null or p.tipo = :tipo)
              and (:estado is null or p.estado = :estado)
            order by p.id
            """)
    List<Poliza> buscar(@Param("tipo") TipoPoliza tipo, @Param("estado") EstadoPoliza estado);

}
