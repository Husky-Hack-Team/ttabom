import os
from decimal import Decimal
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field, field_validator
from supabase import Client, create_client

# Loads backend/.env locally; on Vercel, env vars come from the project settings.
load_dotenv()

app = FastAPI(title="ttabom API")

allowed_origins = ["http://localhost:3000"]
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(APIError)
def supabase_error(request: Request, exc: APIError):
    # Surface Supabase errors (e.g. missing table) instead of a bare 500.
    return JSONResponse(status_code=502, content={"detail": f"Database error: {exc.message}"})


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    # Created lazily so /api/health works without credentials. The client talks
    # to Supabase over HTTP, so there is no persistent DB connection to manage.
    # Accept the REST endpoint too (".../rest/v1/"); the client appends that itself.
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/").removesuffix("/rest/v1")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise HTTPException(
            status_code=500,
            detail="Server is missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.",
        )
    return create_client(url, key)


class TransactionIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(max_digits=12, decimal_places=2)

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Description must not be blank.")
        return value

    @field_validator("amount")
    @classmethod
    def nonzero_amount(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("Amount must not be zero.")
        return value


router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/transactions")
def list_transactions(limit: int = 50):
    limit = max(1, min(limit, 200))
    result = (
        get_supabase()
        .table("transactions")
        .select("id, description, amount, created_at")
        .order("created_at", desc=True)
        .order("id", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@router.post("/transactions", status_code=201)
def create_transaction(tx: TransactionIn):
    result = (
        get_supabase()
        .table("transactions")
        .insert({"description": tx.description, "amount": str(tx.amount)})
        .execute()
    )
    return result.data[0]


@router.get("/balance")
def get_balance():
    result = get_supabase().table("transactions").select("amount").execute()
    total = sum((Decimal(str(row["amount"])) for row in result.data), Decimal("0"))
    return {"balance": float(total)}


app.include_router(router)
