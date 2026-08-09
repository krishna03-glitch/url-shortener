# URL Shortener API

A lightweight URL shortening service built with **FastAPI** and **PostgreSQL**.

## Links

- **Live Portfolio:** https://krishna-portfolio-nine-rose.vercel.app/
- **Project Drive:** https://drive.google.com/drive/folders/1IuRQaw0VLLKtBMHMMHPTHAmFwcCHx5KB?usp=drive_link

---

## Features

- `POST /shorten` — accepts a long URL, returns a unique short code and shortened URL
- `GET /{short_code}` — redirects the caller to the original URL (HTTP 302)
- Idempotent: shortening the same URL twice returns the same code
- Auto-creates the `urls` table on first run
- Interactive API docs at `/docs` (Swagger UI)

---

## Tech Stack

| Layer    | Technology            |
|----------|-----------------------|
| API      | FastAPI 0.111         |
| Server   | Uvicorn               |
| Database | PostgreSQL 16         |
| Driver   | psycopg2-binary       |
| Schemas  | Pydantic v2           |

---

## Project Structure

```
url_shortener/
├── main.py            # FastAPI application
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container image for the API
├── docker-compose.yml # Spins up API + PostgreSQL together
└── README.md
```

---

## Running the Project

### Option 1 — Docker Compose (recommended, no setup needed)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

---

### Option 2 — Local Python + existing PostgreSQL

**1. Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Set the connection string**

```bash
export DATABASE_URL="postgresql://<user>:<password>@localhost:5432/<dbname>"
# Windows PowerShell:
# $env:DATABASE_URL = "postgresql://..."
```

**3. Start the server**

```bash
uvicorn main:app --reload
```

---

## API Usage

### Shorten a URL

```http
POST /shorten
Content-Type: application/json

{
  "url": "https://www.example.com/some/very/long/path?query=true"
}
```

**Response (201 Created)**

```json
{
  "short_url": "http://localhost:8000/aB3xY7q",
  "short_code": "aB3xY7q",
  "original_url": "https://www.example.com/some/very/long/path?query=true"
}
```

---

### Redirect via short code

```http
GET /aB3xY7q
```

Returns HTTP **302 Found** with `Location` header pointing to the original URL.

---

### Validation error (invalid URL)

```http
POST /shorten
Content-Type: application/json

{ "url": "not-a-url" }
```

**Response (422 Unprocessable Entity)**

```json
{
  "detail": [
    {
      "type": "url_parsing",
      "loc": ["body", "url"],
      "msg": "Input should be a valid URL ..."
    }
  ]
}
```

---

## Environment Variables

| Variable       | Default                                              | Description                        |
|----------------|------------------------------------------------------|------------------------------------|
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/urlshortener` | PostgreSQL connection string |
| `BASE_URL`     | `http://localhost:8000`                              | Prefix used to build short URLs    |

---

## Database Schema

```sql
CREATE TABLE urls (
    id          SERIAL PRIMARY KEY,
    short_code  VARCHAR(10) UNIQUE NOT NULL,
    long_url    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

The table is created automatically on startup if it does not already exist.

---

## Interactive Docs

Once the server is running, open:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc:       [http://localhost:8000/redoc](http://localhost:8000/redoc)
