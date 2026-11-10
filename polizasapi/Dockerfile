# --- Etapa 1: compilar el jar con Maven ---
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app

# Descargar dependencias primero para aprovechar la caché de capas
COPY pom.xml .
RUN mvn -B -q dependency:go-offline

COPY src ./src
RUN mvn -B -q package -DskipTests

# --- Etapa 2: imagen liviana solo con el JRE ---
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

RUN addgroup -S app && adduser -S app -G app
USER app

COPY --from=build /app/target/polizasapi-*.jar app.jar

# Limita la memoria de la JVM al contenedor (el plan gratis de Render tiene 512 MB)
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75 -XX:+UseSerialGC"
EXPOSE 8080

ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar app.jar"]
