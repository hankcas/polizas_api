package com.seguros.polizasapi.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.seguros.polizasapi.dto.ErrorResponse;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Exige el header {@code x-api-key} en todos los endpoints de la API.
 * Quedan excluidos la consola de H2 (herramienta de desarrollo), el health check
 * que usa la plataforma de despliegue y la documentación pública (Swagger UI y OpenAPI).
 */
@Component
public class ApiKeyFilter extends OncePerRequestFilter {

    public static final String HEADER_API_KEY = "x-api-key";

    private final byte[] apiKey;
    private final ObjectMapper objectMapper;

    public ApiKeyFilter(@Value("${api.key}") String apiKey, ObjectMapper objectMapper) {
        this.apiKey = apiKey.getBytes(StandardCharsets.UTF_8);
        this.objectMapper = objectMapper;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String ruta = request.getRequestURI().substring(request.getContextPath().length());
        return ruta.equals("/")
                || ruta.equals("/actuator/health")
                || ruta.startsWith("/h2-console")
                || ruta.equals("/swagger-ui.html")
                || ruta.startsWith("/swagger-ui/")
                || ruta.startsWith("/v3/api-docs");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String recibida = request.getHeader(HEADER_API_KEY);

        if (recibida == null || recibida.isBlank()) {
            rechazar(request, response, "Falta el header " + HEADER_API_KEY);
            return;
        }
        // Comparación en tiempo constante para no filtrar información por tiempos de respuesta
        if (!MessageDigest.isEqual(apiKey, recibida.getBytes(StandardCharsets.UTF_8))) {
            rechazar(request, response, "API key inválida");
            return;
        }
        chain.doFilter(request, response);
    }

    private void rechazar(HttpServletRequest request, HttpServletResponse response, String mensaje) throws IOException {
        HttpStatus status = HttpStatus.UNAUTHORIZED;
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        objectMapper.writeValue(response.getWriter(),
                ErrorResponse.of(status.value(), status.getReasonPhrase(), mensaje, request.getRequestURI()));
    }
}
