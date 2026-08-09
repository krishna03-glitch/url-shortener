import os
import random
import string
from contextlib import asynccontextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/urlshortener",
)


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    id          SERIAL PRIMARY KEY,
                    short_code  VARCHAR(10) UNIQUE NOT NULL,
                    long_url    TEXT NOT NULL,
                    created_at  TIMESTAMP DEFAULT NOW()
                );
                """
            )
        conn.commit()


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="URL Shortener API",
    description="Shorten long URLs and redirect via short codes.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_url: str
    short_code: str
    original_url: str


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
CODE_LENGTH = 7
CHARSET = string.ascii_letters + string.digits


def generate_code() -> str:
    return "".join(random.choices(CHARSET, k=CODE_LENGTH))


def unique_code(cur) -> str:
    for _ in range(10):
        code = generate_code()
        cur.execute("SELECT 1 FROM urls WHERE short_code = %s", (code,))
        if not cur.fetchone():
            return code
    raise RuntimeError("Could not generate a unique short code — try again.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(body: ShortenRequest):
    """Accept a long URL and return a shortened URL."""
    long_url = str(body.url)

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Return existing code if URL was already shortened
            cur.execute("SELECT short_code FROM urls WHERE long_url = %s", (long_url,))
            row = cur.fetchone()

            if row:
                code = row["short_code"]
            else:
                code = unique_code(cur)
                cur.execute(
                    "INSERT INTO urls (short_code, long_url) VALUES (%s, %s)",
                    (code, long_url),
                )
        conn.commit()

    return ShortenResponse(
        short_url=f"{BASE_URL}/{code}",
        short_code=code,
        original_url=long_url,
    )


@app.get("/{short_code}", response_class=RedirectResponse, status_code=302)
def redirect(short_code: str):
    """Redirect to the original URL for the given short code."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT long_url FROM urls WHERE short_code = %s", (short_code,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Short code '{short_code}' not found.")

    return row["long_url"]
