FROM python:3.13-alpine

LABEL org.opencontainers.image.source="https://github.com/lxmfy/LXMFy"
LABEL org.opencontainers.image.description="Easily create LXMF bots for the Reticulum Network with this extensible framework."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="LXMFy"

WORKDIR /bot

# Create necessary directories for Reticulum and bot
RUN mkdir -p /root/.reticulum /bot/config

RUN pip3 install --no-cache-dir lxmfy

CMD ["lxmfy", "run", "echo"]
