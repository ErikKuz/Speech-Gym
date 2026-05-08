# ===== Stage 1: build =====
FROM maven:3.9.9-eclipse-temurin-21 AS build

WORKDIR /app

# Сначала копируем только файлы зависимостей, чтобы лучше работал layer cache
COPY pom.xml .
COPY .mvn .mvn
COPY mvnw .

# Если используешь mvnw, раскомментируй:
RUN chmod +x mvnw

# Подтягиваем зависимости заранее
RUN ./mvnw dependency:go-offline -B || mvn dependency:go-offline -B

# Теперь копируем исходники
COPY src src

# Сборка приложения
RUN ./mvnw clean package -DskipTests || mvn clean package -DskipTests

# ===== Stage 2: runtime =====
FROM eclipse-temurin:21-jre

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Папка под локальные аудиофайлы, если пока используешь файловую систему
RUN mkdir -p /data/audio

# Копируем собранный jar
COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
