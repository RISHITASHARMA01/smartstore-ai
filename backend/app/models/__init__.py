from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    role       = Column(String, default="staff")  # "admin" or "staff"
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"
    id                = Column(Integer, primary_key=True, index=True)
    sku               = Column(String, unique=True, index=True, nullable=False)
    name              = Column(String, nullable=False)
    category          = Column(String, nullable=False)
    stock_qty         = Column(Integer, default=0)
    unit_price        = Column(Float, nullable=False)
    reorder_threshold = Column(Integer, default=10)
    expiry_date       = Column(DateTime(timezone=True), nullable=True)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())
    stock_history     = relationship("StockHistory", back_populates="product")

class Supplier(Base):
    __tablename__ = "suppliers"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    email          = Column(String, nullable=False)
    categories     = Column(JSON, default=[])
    lead_time_days = Column(Integer, default=3)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id          = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status      = Column(String, default="Draft")  # Draft→Sent→Acknowledged→Received
    total_value = Column(Float, default=0.0)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
    supplier    = relationship("Supplier", back_populates="purchase_orders")
    line_items  = relationship("POLineItem", back_populates="purchase_order")

class POLineItem(Base):
    __tablename__ = "po_line_items"
    id               = Column(Integer, primary_key=True, index=True)
    po_id            = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id       = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity         = Column(Integer, nullable=False)
    unit_price       = Column(Float, nullable=False)
    purchase_order   = relationship("PurchaseOrder", back_populates="line_items")
    product          = relationship("Product")

class StockHistory(Base):
    __tablename__ = "stock_history"
    id          = Column(Integer, primary_key=True, index=True)
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_qty  = Column(Integer, nullable=False)  # positive=restock, negative=sale
    change_type = Column(String, nullable=False)   # sale, restock, write_off, adjustment
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    product     = relationship("Product", back_populates="stock_history")

class Invoice(Base):
    __tablename__ = "invoices"
    id            = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String, nullable=True)
    invoice_date  = Column(String, nullable=True)
    line_items    = Column(JSON, default=[])
    grand_total   = Column(Float, nullable=True)
    confirmed     = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

class Report(Base):
    __tablename__ = "reports"
    id         = Column(Integer, primary_key=True, index=True)
    type       = Column(String, nullable=False)  # low_stock_po, weekly_summary, expiry_alert
    content    = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
