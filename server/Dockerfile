FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      build-essential \
      libpq-dev \
      python3-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
