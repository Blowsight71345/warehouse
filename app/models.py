from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Enum as SqlalchemyEnum
from sqlalchemy.orm import relationship
import datetime
from database import Base
from enum import Enum

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=1)

class OrderStatus(str, Enum):
    processing = "в процессе"
    shipped = "отправлен"
    delivered = "доставлен"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    status = Column(SqlalchemyEnum(OrderStatus), default=OrderStatus.processing)

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)

    order = relationship("Order", back_populates="items")