FROM rust:1.98.1-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*
# Toolchain setup/builds run as the caller's non-root UID, not this image layer.
WORKDIR /work
