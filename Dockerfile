FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NANOBOT_HOME=/home/app/.nanobot
ENV NANOBOT_CONFIG=/home/app/.nanobot/config.json
ENV NANOBOT_WORKSPACE=/workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin app

WORKDIR /app

ARG NANOBOT_PACKAGE=nanobot-ai==0.1.4.post5
RUN pip install --no-cache-dir "${NANOBOT_PACKAGE}"

COPY docker/entrypoint.sh /app/entrypoint.sh
COPY docker/generate_config.py /app/generate_config.py
COPY docker/sitecustomize.py /app/sitecustomize.py

RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /home/app/.nanobot /workspace \
    && chown -R app:app /app /home/app /workspace

USER app

CMD ["/app/entrypoint.sh"]
