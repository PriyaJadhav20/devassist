FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .
RUN useradd -m app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn devassist.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
