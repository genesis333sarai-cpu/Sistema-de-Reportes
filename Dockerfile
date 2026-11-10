FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PORT=8080
ENV VINTO_DB=sqlite:////app/vinto.db
ENV VINTO_UPLOADS=/app/uploads

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python corregir_vbuild.py

RUN mkdir -p /app/uploads

EXPOSE 8080

CMD ["python", "main.py"]