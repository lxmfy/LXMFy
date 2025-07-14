ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-alpine

LABEL org.opencontainers.image.source="https://github.com/lxmfy/LXMFy"
LABEL org.opencontainers.image.description="Easily create LXMF bots for the Reticulum Network with this extensible framework."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="LXMFy"

WORKDIR /bot

RUN mkdir -p /root/.reticulum /bot/config

COPY . /bot
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir .

CMD ["lxmfy", "run", "echo"]
