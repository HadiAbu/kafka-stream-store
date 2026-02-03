from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import SessionLocal, engine
from app.kafka import KafkaPublisher
from app.models import Base, Order, OrderItem, OrderStatus, User
from app.schemas import OrderCreate, OrderOut, UserCreate, UserOut

app = FastAPI(title="Orders API")

# TEMP: auto-create tables for fast iteration; we'll replace with Alembic.
# Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    app.state.kafka = KafkaPublisher()


@app.on_event("shutdown")
def shutdown() -> None:
    publisher = getattr(app.state, "kafka", None)
    if publisher:
        publisher.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total = sum(item.quantity * item.unit_price for item in payload.items)
    order = Order(
        user_id=payload.user_id,
        status=OrderStatus.CREATED,
        total_amount=total,
        currency=payload.currency.upper(),
    )

    for item in payload.items:
        order.items.append(
            OrderItem(
                product_sku=item.product_sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )

    db.add(order)
    db.commit()
    db.refresh(order)

    publisher = getattr(app.state, "kafka", None)
    if publisher:
        publisher.publish_order_created(order)

    return order


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
