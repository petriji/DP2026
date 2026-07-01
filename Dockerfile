FROM ghcr.io/xu-cheng/texlive-debian:latest

# Base image is Debian (trixie-slim) — see xu-cheng/latex-docker Dockerfile.debian.
# NOTE: "texlive-full" is a deprecated legacy tag that resolves to an Alpine/musl
# image (apk-based); it is NOT used here because this project's Python stack
# (numpy, pandas, scipy, matplotlib, geopandas, shapely) relies on glibc-only
# manylinux pip wheels that are unreliable/unavailable to build on musl.
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        git \
        make \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash --uid 1000 thesis

USER thesis
WORKDIR /workspace/DP2026

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["bash"]
