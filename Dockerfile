FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Usuario sin privilegios.
RUN useradd --create-home finbot
USER finbot

EXPOSE 8080

# Forma shell para expandir $PORT; exec deja a uvicorn como PID 1 y recibe las señales de Cloud Run.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
