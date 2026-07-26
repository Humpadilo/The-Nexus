ARG BUILD_FROM=python:3.12-slim-bookworm
FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.1.0
ARG BUILD_ARCH=amd64
LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY archivist ./archivist
COPY rootfs /
RUN chmod +x /usr/local/bin/archivist

EXPOSE 8099
CMD ["/usr/local/bin/archivist"]
