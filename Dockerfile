FROM python:3.13-slim

WORKDIR /bot

COPY examples/test-bot.py /bot/test-bot.py

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "test-bot.py"]

