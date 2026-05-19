# polizas_api
# API Gestión de Pólizas

API REST desarrollada con Spring Boot para la gestión de pólizas y riesgos.

## Tecnologías

- Java 17
- Spring Boot
- Spring Data JPA
- Maven
- H2 Database
- Lombok

---

# Funcionalidades

## Pólizas

- Consultar pólizas por tipo y estado
- Renovar póliza
- Cancelar póliza

## Riesgos

- Consultar riesgos de una póliza
- Agregar riesgos
- Cancelar riesgos

## CORE Mock

- Endpoint mock para simular integración con CORE transaccional

---

# Reglas de negocio

- Una póliza individual solo puede tener un riesgo
- No se puede renovar una póliza cancelada
- Cancelar una póliza cancela todos sus riesgos
- Solo pólizas colectivas permiten agregar riesgos

---

# Seguridad

Todos los endpoints requieren header:

```http
x-api-key: 123456

# Nota

Por temas de tiempo no fue posible completar al 100% toda la implementación ni dejar completamente funcional cada endpoint.  

Sin embargo, se desarrolló la estructura principal del proyecto siguiendo arquitectura por capas con Spring Boot, incluyendo entidades, controladores, servicios, repositorios, enums y configuración base de la API.

También se implementó parte de las reglas de negocio solicitadas y la estructura necesaria para continuar la solución.

El objetivo fue priorizar organización, separación de responsabilidades y aproximación técnica acorde a la prueba planteada.

Agradezco el tiempo de revisión y espero haber logrado demostrar criterio técnico, capacidad de análisis y enfoque de solución durante el desarrollo de la prueba.
