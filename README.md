# Pinboard — Mapbox marker editor

SPA для розміщення та редагування маркерів на Mapbox-карті. Бекенд написаний
на Python/FastAPI, дані зберігаються в пам'яті процесу — база даних для цього
тестового завдання не потрібна.

## Можливості

- клік по карті створює маркер із початковим score `0`;
- score від `0` до `5` змінює колір маркера: black, gray, red, orange, lime,
  green;
- маркер можна перетягувати та змінювати його score у popup;
- маркери можна видаляти;
- панель у правому верхньому куті показує загальну кількість і розподіл за
  score;
- імпорт та експорт JSON;
- створення маркера може випадково завершитися `503`, після чого UI показує
  помилку й не додає маркер локально.

## Запуск локально

Потрібен Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
$env:MARKER_FAILURE_RATE="0.2"
$env:MAPBOX_TOKEN="your-mapbox-public-token"
python -m map_app
```

Відкрийте <http://localhost:8000>. Mapbox token передається в браузер через
`MAPBOX_TOKEN`; для локальної розробки його можна покласти у некомітну `.env`
файл. Публічний token з умови тестового завдання підходить для цього поля.

`MARKER_FAILURE_RATE` — число від `0` до `1`; наприклад, `0` вимикає штучні
збої, а `1` відхиляє кожне створення маркера. За замовчуванням використовується
`0.2`.

## API

| Метод | URL | Призначення |
| --- | --- | --- |
| `GET` | `/api/health` | health check |
| `GET` | `/api/markers` | отримати всі маркери |
| `POST` | `/api/markers` | створити маркер; може повернути `503` |
| `PATCH` | `/api/markers/{id}` | оновити score та/або coordinates |
| `DELETE` | `/api/markers/{id}` | видалити маркер |

Приклад payload:

```json
{
  "coordinates": { "lng": 30.5234, "lat": 50.4501 },
  "score": 4
}
```

Swagger-документація доступна за адресою `/docs`.

## Docker

```powershell
docker build -t pinboard .
docker run --rm -p 8000:8000 -e MARKER_FAILURE_RATE=0.2 pinboard
```

Або через Compose:

```powershell
docker compose up --build
```

## Тести та перевірки

```powershell
pytest -q
python -m compileall -q src
```

Тести не викликають Mapbox або інші зовнішні сервіси: вони перевіряють API,
валідацію, CRUD, штучний збій і роздачу frontend.

## Структура

```text
frontend/
  index.html              # shell SPA
  assets/app.js           # Mapbox UI, CRUD, import/export
  assets/styles.css       # responsive dark UI
src/map_app/
  main.py                 # FastAPI app and routes
  models.py               # validated API contracts
  repository.py           # thread-safe in-memory storage
  failure.py              # injectable random failure policy
tests/test_api.py         # offline API tests
```
