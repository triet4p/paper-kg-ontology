# docker/fuseki/Dockerfile
FROM eclipse-temurin:21-jre-jammy

ARG JENA_VERSION=6.1.0
WORKDIR /opt

RUN apt-get update && \
    apt-get install -y --no-install-recommends wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Full Jena distro: contains riot, tdb2.tdbloader, shacl CLI tools
RUN wget -q https://dlcdn.apache.org/jena/binaries/apache-jena-${JENA_VERSION}.tar.gz && \
    tar xzf apache-jena-${JENA_VERSION}.tar.gz && \
    mv apache-jena-${JENA_VERSION} jena && \
    rm apache-jena-${JENA_VERSION}.tar.gz

# Fuseki server distro
RUN wget -q https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-${JENA_VERSION}.tar.gz && \
    tar xzf apache-jena-fuseki-${JENA_VERSION}.tar.gz && \
    mv apache-jena-fuseki-${JENA_VERSION} fuseki && \
    rm apache-jena-fuseki-${JENA_VERSION}.tar.gz

ENV PATH="/opt/jena/bin:/opt/fuseki:${PATH}"
ENV FUSEKI_BASE=/data/fuseki-base

WORKDIR /opt/fuseki
EXPOSE 3030
CMD ["./fuseki-server"]