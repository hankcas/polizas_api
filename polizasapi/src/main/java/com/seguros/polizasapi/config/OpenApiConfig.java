package com.seguros.polizasapi.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.tags.Tag;
import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import static com.seguros.polizasapi.config.ApiKeyFilter.HEADER_API_KEY;

/**
 * Documentación OpenAPI (Swagger UI en /swagger-ui.html).
 * Declara el esquema de seguridad por API key para que el botón "Authorize" la envíe en cada petición.
 */
@Configuration
public class OpenApiConfig {

    private static final String ESQUEMA_API_KEY = "apiKey";
    private static final List<String> ORDEN_SECCIONES = List.of("Pólizas", "Riesgos", "CORE mock");

    @Bean
    public OpenAPI polizasOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("API Gestión de Pólizas")
                        .version("1.0.0")
                        .description("""
                                API REST para gestionar pólizas de seguro y sus riesgos.

                                **Cómo probarla:** haz clic en **Authorize**, escribe la API key `123456` \
                                y luego usa **Try it out** en cualquier endpoint.

                                **Reglas de negocio**
                                - Solo las pólizas colectivas permiten agregar riesgos (una individual tiene un único riesgo).
                                - No se puede renovar una póliza cancelada.
                                - Cancelar una póliza cancela todos sus riesgos.
                                - Al renovar, el canon y la prima se incrementan según el IPC y la vigencia se extiende un año.

                                Los datos son de ejemplo y se reinician cuando el servicio se reinicia."""))
                .components(new Components().addSecuritySchemes(ESQUEMA_API_KEY, new SecurityScheme()
                        .type(SecurityScheme.Type.APIKEY)
                        .in(SecurityScheme.In.HEADER)
                        .name(HEADER_API_KEY)
                        .description("API key de la demo: 123456")))
                .addSecurityItem(new SecurityRequirement().addList(ESQUEMA_API_KEY));
    }

    /**
     * springdoc ordena las secciones alfabéticamente; aquí se fija el orden en que
     * aparecen en Swagger UI: primero Pólizas, luego Riesgos y al final el CORE mock.
     */
    @Bean
    public OpenApiCustomizer ordenarSecciones() {
        return openApi -> {
            if (openApi.getTags() == null) {
                return;
            }
            List<Tag> ordenadas = new ArrayList<>(openApi.getTags());
            ordenadas.sort(Comparator.comparingInt(tag -> {
                int posicion = ORDEN_SECCIONES.indexOf(tag.getName());
                return posicion < 0 ? Integer.MAX_VALUE : posicion;
            }));
            openApi.setTags(ordenadas);
        };
    }
}
