FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsqlcipher-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlcipher-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash soulavatar

COPY --from=builder /root/.local /home/soulavatar/.local
ENV PATH="/home/soulavatar/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/data /app/models /app/proto /app/config /app/src /app/scripts
COPY . /app/
RUN chown -R soulavatar:soulavatar /app

WORKDIR /app
USER soulavatar

EXPOSE 50051
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["python", "-m", "src"]
CMD ["serve"]
