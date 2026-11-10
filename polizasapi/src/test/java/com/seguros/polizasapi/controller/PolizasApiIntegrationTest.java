package com.seguros.polizasapi.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Pruebas de punta a punta sobre los datos de data.sql.
 * Cada prueba corre en una transacción que se revierte al final.
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class PolizasApiIntegrationTest {

    private static final String API_KEY = "x-api-key";
    private static final String VALOR_API_KEY = "123456";

    @Autowired
    private MockMvc mvc;

    @Test
    void sinApiKeyResponde401() throws Exception {
        mvc.perform(get("/polizas"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.mensaje", containsString("x-api-key")));
    }

    @Test
    void apiKeyInvalidaResponde401() throws Exception {
        mvc.perform(get("/polizas").header(API_KEY, "otra"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.mensaje").value("API key inválida"));
    }

    @Test
    void healthCheckNoRequiereApiKey() throws Exception {
        mvc.perform(get("/actuator/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }

    @Test
    void otrosEndpointsDeActuatorNoEstanExpuestos() throws Exception {
        mvc.perform(get("/actuator/env").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isNotFound());
    }

    @Test
    void listarSinFiltrosDevuelveTodas() throws Exception {
        mvc.perform(get("/polizas").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(5)));
    }

    @Test
    void listarFiltraPorTipoYEstado() throws Exception {
        mvc.perform(get("/polizas").param("tipo", "COLECTIVA").param("estado", "ACTIVA").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[*].tipo", everyItem(is("COLECTIVA"))))
                .andExpect(jsonPath("$[0].riesgosActivos").value(3));
    }

    @Test
    void filtroConValorInvalidoResponde400() throws Exception {
        mvc.perform(get("/polizas").param("tipo", "OTRO").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.mensaje", containsString("INDIVIDUAL")));
    }

    @Test
    void polizaInexistenteResponde404() throws Exception {
        mvc.perform(get("/polizas/999").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isNotFound());
    }

    @Test
    void renovarPolizaActiva() throws Exception {
        mvc.perform(post("/polizas/1/renovar").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.estado").value("RENOVADA"))
                .andExpect(jsonPath("$.canonMensual").value(1578000.00))
                .andExpect(jsonPath("$.fechaFin").value("2027-01-01"));
    }

    @Test
    void renovarPolizaCanceladaResponde422() throws Exception {
        mvc.perform(post("/polizas/3/renovar").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.mensaje").value("No se puede renovar una póliza cancelada"));
    }

    @Test
    void cancelarPolizaCancelaSusRiesgos() throws Exception {
        mvc.perform(post("/polizas/2/cancelar").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.estado").value("CANCELADA"))
                .andExpect(jsonPath("$.riesgosActivos").value(0));

        mvc.perform(get("/polizas/2/riesgos").header(API_KEY, VALOR_API_KEY))
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(jsonPath("$[*].estado", everyItem(is("CANCELADO"))));
    }

    @Test
    void agregarRiesgoAPolizaColectiva() throws Exception {
        mvc.perform(post("/polizas/2/riesgos")
                        .header(API_KEY, VALOR_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"descripcion": "Bodega sur", "direccion": "Calle 13 # 68-90", "valorAsegurado": 1800000}
                                """))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", containsString("/riesgos/")))
                .andExpect(jsonPath("$.polizaId").value(2))
                .andExpect(jsonPath("$.estado").value("ACTIVO"));

        mvc.perform(get("/polizas/2/riesgos").header(API_KEY, VALOR_API_KEY))
                .andExpect(jsonPath("$", hasSize(4)));
    }

    @Test
    void agregarRiesgoAPolizaIndividualResponde422() throws Exception {
        mvc.perform(post("/polizas/1/riesgos")
                        .header(API_KEY, VALOR_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"descripcion": "Garaje", "direccion": "Calle 1", "valorAsegurado": 100000}
                                """))
                .andExpect(status().isUnprocessableEntity());
    }

    @Test
    void agregarRiesgoInvalidoResponde400ConDetalles() throws Exception {
        mvc.perform(post("/polizas/2/riesgos")
                        .header(API_KEY, VALOR_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"descripcion": "", "valorAsegurado": -5}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detalles", hasSize(3)));
    }

    @Test
    void cancelarRiesgo() throws Exception {
        mvc.perform(post("/riesgos/2/cancelar").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.estado").value("CANCELADO"));

        mvc.perform(post("/riesgos/2/cancelar").header(API_KEY, VALOR_API_KEY))
                .andExpect(status().isUnprocessableEntity());
    }

    @Test
    void coreMockRecibeEventos() throws Exception {
        mvc.perform(post("/core-mock/eventos")
                        .header(API_KEY, VALOR_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"tipoEvento": "POLIZA_RENOVADA", "polizaId": 1}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.estado").value("RECIBIDO"))
                .andExpect(jsonPath("$.idTransaccion").isNotEmpty());
    }
}
