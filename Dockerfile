FROM ghcr.io/xu-cheng/texlive-historic-debian:2023

# Base image is Debian (bookworm) — see xu-cheng/latex-docker Dockerfile.debian.
# Pinned to the historic TeX Live 2023 tag (pdfTeX 1.40.25, biber 2.19) to match
# the version this thesis's CTUthesis.cls/biblatex-iso690 stack is developed and
# tested against. The rolling "latest" tag currently resolves to TeX Live 2026
# (pdfTeX 1.40.29, biber 2.21), whose newer biblatex breaks the class's custom
# citation-subindexing expl3 code (\ctu_assign_displaylabel:o accessing
# \abx@field@entrykey), causing a fatal compile error at \maketitle with raw
# biblatex internal name-list fields (family=, hash=) leaking into the PDF.
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

# Pre-create the workdir (with a placeholder .venv) owned by the non-root
# `thesis` user. Docker initializes a fresh anonymous/named volume mounted at
# this path from the image's existing directory content/ownership, so this
# avoids "Permission denied" when tools/docker_verify_full_build.sh creates
# the venv under a volume-mounted /workspace/DP2026/.venv.
RUN mkdir -p /workspace/DP2026/.venv && chown -R thesis:thesis /workspace/DP2026

USER thesis
WORKDIR /workspace/DP2026

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["bash"]
