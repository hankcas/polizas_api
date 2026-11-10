package com.seguros.polizasapi.core;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionalEventListener;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import static com.seguros.polizasapi.config.ApiKeyFilter.HEADER_API_KEY;

/**
 * Cliente HTTP hacia el CORE transaccional.
 * <p>
 * Escucha los {@link EventoCore} publicados por los servicios y los envía solo después
 * de que la transacción hace commit, de modo que el CORE nunca recibe cambios revertidos.
 * Una falla del CORE se registra en el log pero no revierte la operación ya confirmada.
 */
@Slf4j
@Component
public class CoreClient {

    private final RestClient restClient;
    private final String coreUrl;

    public CoreClient(RestClient.Builder builder,
                      @Value("${core.url}") String coreUrl,
                      @Value("${api.key}") String apiKey) {
        this.coreUrl = coreUrl;
        this.restClient = builder.defaultHeader(HEADER_API_KEY, apiKey).build();
    }

    @TransactionalEventListener
    public void notificar(EventoCore evento) {
        try {
            restClient.post()
                    .uri(coreUrl)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(evento)
                    .retrieve()
                    .toBodilessEntity();
            log.info("Evento {} notificado al CORE (póliza {})", evento.tipoEvento(), evento.polizaId());
        } catch (RestClientException ex) {
            log.warn("No fue posible notificar el evento {} al CORE: {}", evento.tipoEvento(), ex.getMessage());
        }
    }
}
