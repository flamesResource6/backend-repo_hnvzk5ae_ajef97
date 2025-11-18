import os
from typing import List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import FlowerProduct, Order

app = FastAPI(title="Blossom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Utilities ----------

def to_json(doc: dict) -> dict:
    """Convert Mongo document to JSON-serializable dict"""
    if not doc:
        return doc
    d = {**doc}
    _id = d.get("_id")
    if _id is not None:
        d["_id"] = str(_id)
    # Convert datetimes to isoformat if present
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            try:
                d[k] = v.isoformat()
            except Exception:
                pass
    return d


# ---------- Health ----------

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    # Env vars
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ---------- Products ----------

SAMPLE_PRODUCTS: List[FlowerProduct] = [
    FlowerProduct(
        name="Pink Peony Bliss",
        description="Lush pink peonies with delicate greenery.",
        price=49.0,
        image_url="https://images.unsplash.com/photo-1464965911861-746a04b4bca6?q=80&w=1600&auto=format&fit=crop",
        tags=["peony", "pink"],
    ),
    FlowerProduct(
        name="Rosy Romance",
        description="Classic long-stemmed roses in soft blush.",
        price=59.0,
        image_url="https://images.unsplash.com/photo-1523661149972-0becaca2016e?q=80&w=1600&auto=format&fit=crop",
        tags=["rose", "romance"],
    ),
    FlowerProduct(
        name="Spring Meadow",
        description="Seasonal mix with pastel tones and wild sprigs.",
        price=39.0,
        image_url="https://images.unsplash.com/photo-1495433324511-bf8e92934d90?q=80&w=1600&auto=format&fit=crop",
        tags=["seasonal", "pastel"],
    ),
]


@app.get("/api/products")
def list_products() -> List[dict]:
    if db is None:
        # Provide graceful empty list to avoid frontend crash
        return []
    docs = get_documents("flowerproduct")
    # If empty, return empty list; frontend may call /api/seed first
    return [to_json(d) for d in docs]


@app.post("/api/seed")
def seed_products():
    if db is None:
        # When database not configured, respond with message but don't fail
        return {"inserted": 0, "message": "Database not configured; skipping seed."}

    existing = db["flowerproduct"].count_documents({})
    inserted = 0
    if existing == 0:
        for p in SAMPLE_PRODUCTS:
            create_document("flowerproduct", p)
            inserted += 1
    return {"inserted": inserted, "total": db["flowerproduct"].count_documents({})}


# ---------- Orders ----------

class OrderResponse(BaseModel):
    id: str
    status: str = "received"


@app.post("/api/orders", response_model=OrderResponse)
def create_order(order: Order):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    # Basic total validation to avoid mismatch
    calc_total = sum(item.price * item.qty for item in order.items)
    if abs(calc_total - order.total) > 0.01:
        raise HTTPException(status_code=400, detail="Total does not match items")

    oid = create_document("order", order)
    return OrderResponse(id=oid, status="received")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
