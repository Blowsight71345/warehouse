from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import get_db, Base, engine
from typing import List

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductBase, db: Session = Depends(get_db)):
    try:
        db_product = models.Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products


@app.get("/products/{id}", response_model=schemas.Product)
def read_product(id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{id}", response_model=schemas.Product)
def update_product(id: int, product: schemas.ProductBase, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted"}


@app.post("/orders/", response_model=schemas.Order)
def create_order(order: schemas.OrderBase, db: Session = Depends(get_db)):
    if order.status not in [status.value for status in models.OrderStatus]:
        raise HTTPException(status_code=400,
                            detail=f"Invalid order status: {order.status}\n"
                                   f"Valid statuses: {[status.value for status in models.OrderStatus]}")
    items_to_add = []
    total_items_valid = True
    error_messages = []

    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()

        if product is None:
            error_messages.append(f"Product {item.product_id} not found")
            total_items_valid = False
        elif product.stock < item.quantity:
            error_messages.append(
                f"Product {item.product_id} not enough stock for quantity {item.quantity}"
            )
            total_items_valid = False
        else:
            items_to_add.append((product, item.quantity))

    if not total_items_valid:
        raise HTTPException(status_code=400, detail=error_messages)

    try:
        db_order = models.Order(status=order.status)
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        for product, quantity in items_to_add:
            db_item = models.OrderItem(order_id=db_order.id,
                                       product_id=product.id,
                                       quantity=quantity)
            db.add(db_item)
            product.stock -= quantity
        db.commit()
        return db_order
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,
                            detail="An error occurred while creating the order.")


@app.get("/orders/", response_model=List[schemas.Order])
def read_orders(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders


@app.get("/orders/{id}", response_model=schemas.Order)
def read_order(id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/orders/{id}/status", response_model=schemas.Order)
def update_order_status(id: int, order_status: schemas.OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order_status.status not in models.OrderStatus:
        raise HTTPException(status_code=400,
                            detail=f"Invalid order status: {order_status.statu}\n"
                                   f"Valid statuses:{[status.value for status in models.OrderStatus]}")
    order.status = order_status.status
    db.commit()
    db.refresh(order)
    return order
