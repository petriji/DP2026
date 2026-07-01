FROM ghcr.io/xu-cheng/texlive-full:latest

# Base image is Arch Linux (xu-cheng/texlive-docker) — use pacman, not apt-get.
RUN pacman -Sy --noconfirm --needed \
        python \
        python-pip \
        git \
        make \
        base-devel \
        ca-certificates \
        curl \
    && pacman -Scc --noconfirm

RUN useradd --create-home --shell /bin/bash --uid 1000 thesis

USER thesis
WORKDIR /workspace/DP2026

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["bash"]
