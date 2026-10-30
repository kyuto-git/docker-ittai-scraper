FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends locales curl && \
    sed -i '/ja_JP.UTF-8/s/^# //g' /etc/locale.gen && locale-gen && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=ja_JP.UTF-8
ENV LC_ALL=ja_JP.UTF-8
ENV PYTHONUNBUFFERED=1
ENV SCRAPE_DELAY=2.0

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/app/
RUN mkdir -p /app/input /app/output /app/logs

CMD ["python", "-m", "app.main"]