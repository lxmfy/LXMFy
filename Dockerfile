FROM python:3.13-slim

WORKDIR /bot

# Create necessary directories for Reticulum and bot
RUN mkdir -p /root/.reticulum /bot/config

COPY examples/test_bot.py /bot/test_bot.py
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

# Default command
CMD ["python3", "test_bot.py"]
