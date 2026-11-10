# API Gestión de Pólizas

API REST desarrollada con Spring Boot para gestionar pólizas de seguro y sus riesgos, con reglas de negocio, seguridad por API key e integración simulada con un CORE transaccional.

## Tecnologías

- Java 17+
- Spring Boot 3.5 (Web, Data JPA, Validation)
- H2 Database (en memoria, con datos de ejemplo)
- Lombok
- JUnit 5, Mockito y MockMvc
- Maven (incluye wrapper, no hace falta instalarlo)

## Cómo ejecutarlo

```bash
cd polizasapi
./mvnw spring-boot:run
```

La API queda en `http://localhost:8080`. En Windows se usa `mvnw.cmd spring-boot:run`.

Para correr las pruebas:

```bash
./mvnw test
```

## Seguridad

Todos los endpoints exigen el header:

```http
x-api-key: 123456
```

Si el header falta o no coincide, la API responde `401 Unauthorized`. La clave se configura en `application.properties` (`api.key`).

## Endpoints

### Pólizas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/polizas?tipo=&estado=` | Lista pólizas. Los filtros `tipo` (`INDIVIDUAL`, `COLECTIVA`) y `estado` (`ACTIVA`, `CANCELADA`, `RENOVADA`) son opcionales |
| GET | `/polizas/{id}` | Consulta una póliza |
| POST | `/polizas/{id}/renovar` | Renueva la póliza por un año y aplica el IPC al canon y a la prima |
| POST | `/polizas/{id}/cancelar` | Cancela la póliza y todos sus riesgos |

### Riesgos

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/polizas/{id}/riesgos` | Lista los riesgos de una póliza |
| POST | `/polizas/{id}/riesgos` | Agrega un riesgo (solo pólizas colectivas) |
| POST | `/riesgos/{id}/cancelar` | Cancela un riesgo |

Cuerpo para agregar un riesgo:

```json
{
  "descripcion": "Bodega sur",
  "direccion": "Calle 13 # 68-90, Bogotá",
  "valorAsegurado": 1800000
}
```

### CORE mock

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/core-mock/eventos` | Simula el CORE transaccional y recibe eventos |
| GET | `/core-mock/eventos` | Lista los eventos recibidos (sirve para verificar la integración) |

Cada renovación o cancelación de póliza, y cada riesgo agregado o cancelado, envía un evento (`POLIZA_RENOVADA`, `POLIZA_CANCELADA`, `RIESGO_AGREGADO`, `RIESGO_CANCELADO`) al CORE por HTTP. El evento sale **después del commit** de la transacción, así el CORE nunca recibe un cambio revertido. Si el CORE no responde, se registra una advertencia y la operación se mantiene. La URL se configura con `core.url`.

## Reglas de negocio

- Una póliza individual solo puede tener un riesgo.
- Solo las pólizas colectivas permiten agregar riesgos.
- No se pueden agregar riesgos a una póliza cancelada.
- No se puede renovar una póliza cancelada.
- Al renovar, el canon mensual y la prima se incrementan según el `porcentajeIpc` de la póliza, y la vigencia se extiende un año.
- Cancelar una póliza cancela todos sus riesgos.
- No se puede cancelar dos veces una póliza ni un riesgo.

## Manejo de errores

Todas las respuestas de error tienen el mismo formato:

```json
{
  "timestamp": "2026-11-10T10:15:30",
  "status": 422,
  "error": "Unprocessable Entity",
  "mensaje": "No se puede renovar una póliza cancelada",
  "path": "/polizas/3/renovar",
  "detalles": []
}
```

| Código | Caso |
|---|---|
| 400 | Campos inválidos (en `detalles`), JSON mal formado o valor de filtro inválido |
| 401 | API key ausente o inválida |
| 404 | Póliza, riesgo o ruta inexistente |
| 422 | Violación de una regla de negocio |

## Datos de ejemplo

Al iniciar se cargan desde `data.sql`:

| Id | Tipo | Estado | Riesgos |
|---|---|---|---|
| 1 | INDIVIDUAL | ACTIVA | 1 |
| 2 | COLECTIVA | ACTIVA | 3 |
| 3 | COLECTIVA | CANCELADA | 1 (cancelado) |
| 4 | INDIVIDUAL | RENOVADA | 1 |
| 5 | COLECTIVA | ACTIVA | 2 |

La consola de H2 está disponible en `http://localhost:8080/h2-console` (JDBC URL `jdbc:h2:mem:polizasdb`, usuario `sa`, sin contraseña).

## Ejemplos

```bash
curl -H "x-api-key: 123456" "http://localhost:8080/polizas?tipo=COLECTIVA&estado=ACTIVA"
```

```bash
curl -X POST -H "x-api-key: 123456" http://localhost:8080/polizas/1/renovar
```

```bash
curl -X POST -H "x-api-key: 123456" -H "Content-Type: application/json" -d '{"descripcion":"Bodega sur","direccion":"Calle 13 # 68-90","valorAsegurado":1800000}' http://localhost:8080/polizas/2/riesgos
```

## Estructura

```
polizasapi/src/main/java/com/seguros/polizasapi
├── config/       Filtro de API key
├── controller/   Pólizas, riesgos y CORE mock
├── core/         Eventos y cliente HTTP hacia el CORE
├── dto/          Contratos de entrada y salida
├── entity/       Entidades JPA
├── enums/        Tipos y estados
├── exception/    Excepciones y manejador global
├── repository/   Repositorios Spring Data
└── service/      Lógica y reglas de negocio
```

## Pruebas

26 pruebas automatizadas:

- **Unitarias** (`PolizaServiceTest`, `RiesgoServiceTest`): reglas de negocio, cálculo del IPC y publicación de eventos.
- **Integración** (`PolizasApiIntegrationTest`): endpoints de punta a punta con MockMvc, seguridad, validaciones y códigos de error.
