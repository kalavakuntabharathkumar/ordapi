from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models, schemas, cache

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Retail Distributor Order & Inventory API", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/products", response_model=list[schemas.ProductOut])
def list_products(q: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    key=f"products:{q or ''}:{offset}:{limit}"
    cached=cache.get_json(key)
    if cached is not None: return cached
    stmt=select(models.Product).order_by(models.Product.id).offset(offset).limit(limit)
    if q: stmt=stmt.where(models.Product.name.ilike(f"%{q}%"))
    rows=list(db.scalars(stmt).all())
    result=[schemas.ProductOut.model_validate(x).model_dump() for x in rows]
    cache.set_json(key,result)
    return result

@app.post("/products", response_model=schemas.ProductOut, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session=Depends(get_db)):
    row=models.Product(**payload.model_dump()); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError: db.rollback(); raise HTTPException(409,"SKU already exists")
    cache.delete_pattern("products:*")
    return row

@app.get("/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session=Depends(get_db)):
    row=db.get(models.Product,product_id)
    if not row: raise HTTPException(404,"Product not found")
    return row

@app.patch("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, payload: schemas.ProductPatch, db: Session=Depends(get_db)):
    row=db.get(models.Product,product_id)
    if not row: raise HTTPException(404,"Product not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(row,k,v)
    db.commit(); db.refresh(row); cache.delete_pattern("products:*"); return row

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session=Depends(get_db)):
    row=db.get(models.Product,product_id)
    if not row: raise HTTPException(404,"Product not found")
    if db.scalar(select(models.OrderItem).where(models.OrderItem.product_id==product_id)):
        raise HTTPException(409,"Product is referenced by an order")
    db.delete(row); db.commit(); cache.delete_pattern("products:*"); return Response(status_code=204)

@app.post("/orders", response_model=schemas.OrderOut, status_code=201)
def create_order(payload: schemas.OrderCreate, db: Session=Depends(get_db)):
    # Validate all inventory before mutating any stock.
    requested={}
    for item in payload.items: requested[item.product_id]=requested.get(item.product_id,0)+item.quantity
    products={pid:db.get(models.Product,pid) for pid in requested}
    for pid,qty in requested.items():
        if products[pid] is None: raise HTTPException(404,f"Product {pid} not found")
        if products[pid].quantity < qty: raise HTTPException(409,f"Insufficient stock for product {pid}")
    order=models.Order(customer_name=payload.customer_name,status="pending",total=0)
    db.add(order); db.flush(); total=0.0
    for pid,qty in requested.items():
        product=products[pid]; product.quantity-=qty; total+=product.price*qty
        order.items.append(models.OrderItem(product_id=pid,quantity=qty,unit_price=product.price))
    order.total=round(total,2); db.commit(); db.refresh(order); cache.delete_pattern("products:*"); return order

@app.get("/orders", response_model=list[schemas.OrderOut])
def list_orders(status: str | None=None, offset: int=Query(0,ge=0), limit: int=Query(50,ge=1,le=200), db: Session=Depends(get_db)):
    stmt=select(models.Order).order_by(models.Order.id.desc()).offset(offset).limit(limit)
    if status: stmt=stmt.where(models.Order.status==status)
    return list(db.scalars(stmt).all())

@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session=Depends(get_db)):
    row=db.get(models.Order,order_id)
    if not row: raise HTTPException(404,"Order not found")
    return row

@app.patch("/orders/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(order_id: int, payload: schemas.OrderStatusPatch, db: Session=Depends(get_db)):
    allowed={"pending","confirmed","shipped","delivered","cancelled"}
    if payload.status not in allowed: raise HTTPException(422,f"Status must be one of {sorted(allowed)}")
    row=db.get(models.Order,order_id)
    if not row: raise HTTPException(404,"Order not found")
    if row.status in {"delivered","cancelled"} and row.status != payload.status: raise HTTPException(409,"Terminal order status cannot be changed")
    row.status=payload.status; db.commit(); db.refresh(row); return row
