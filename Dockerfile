FROM python:3.13-slim

WORKDIR /bot

# Create necessary directories for Reticulum and bot
RUN mkdir -p /root/.reticulum /bot/config

RUN pip3 install --no-cache-dir lxmfy

CMD ["lxmfy", "create", "mybot"]

# Run bot
CMD ["python3", "mybot.py"]
