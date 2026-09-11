FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY frontend ./frontend
RUN pip install --no-cache-dir .

RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["python", "-m", "map_app"]
