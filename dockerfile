FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8000

CMD ["fastapi", "run", "src/tit_stream/database_api.py", "--host", "0.0.0.0", "--port", "8000"]
