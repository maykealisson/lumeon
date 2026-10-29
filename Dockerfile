FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependências Python (camada reaproveitada enquanto o requirements.txt não mudar)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar código da aplicação (o .dockerignore deixa de fora .venv, .env, testes etc.)
COPY . .

# Rodar sem root; o yfinance grava cache em ~/.cache
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)"

# O banco é configurado pelas variáveis MYSQL_* (ou DATABASE_URL) no docker-compose
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
