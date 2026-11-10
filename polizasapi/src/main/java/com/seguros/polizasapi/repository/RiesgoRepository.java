package com.seguros.polizasapi.repository;

import com.seguros.polizasapi.entity.Riesgo;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface RiesgoRepository extends JpaRepository<Riesgo, Long> {

    List<Riesgo> findByPolizaIdOrderByIdAsc(Long polizaId);

}
