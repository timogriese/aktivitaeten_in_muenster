# Build from the repository root so the shared/ tag vocabulary is available:
#   docker build -f backend/Dockerfile -t aktivitaeten-backend .
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build/backend

COPY backend/pom.xml ./
RUN mvn -q -B -DskipTests dependency:go-offline || true

COPY backend/src ./src
COPY shared/tags.json /build/shared/tags.json
COPY shared/tag_images.json /build/shared/tag_images.json
RUN mvn -q -B -DskipTests package

FROM eclipse-temurin:17-jre AS runtime
WORKDIR /app
COPY --from=build /build/backend/target/backend-0.0.1-SNAPSHOT.jar app.jar

# The SQLite database and the OSM extract / graph cache are mounted at runtime, see docker-compose.yml.
ENV DATABASE_PATH=/data/activities.db \
    ROUTING_OSM_FILE=/data/osm/muenster-regbez.osm.pbf \
    ROUTING_GRAPH_DIRECTORY=/data/graph

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
