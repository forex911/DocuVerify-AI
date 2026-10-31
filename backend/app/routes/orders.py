"""
Orders API endpoints for managing approved customer purchase orders.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Order, OrderItem
from app.schemas.order import OrderCreate, OrderResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/orders", tags=["Approved Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, summary="Create Approved Customer Order")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    Creates an authoritative customer order to serve as the ground-truth baseline for verification.
    """
    order_id = payload.order_id or payload.order_number or f"ORD-{payload.customer_name[:3].upper()}-01"
    
    # Check duplicate
    existing = db.query(Order).filter(Order.id == order_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order with ID '{order_id}' already exists.",
        )

    order = Order(
        id=order_id,
        order_number=payload.order_number or order_id,
        customer_name=payload.customer_name,
        currency=payload.currency.upper(),
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        subtotal=payload.subtotal,
        tax=payload.tax,
        freight=payload.freight,
        grand_total=payload.grand_total,
        destination=payload.destination,
        package_count=payload.package_count,
        notes=payload.notes,
        is_authoritative=payload.is_authoritative,
        version=1,
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        order_item = OrderItem(
            order_id=order.id,
            sku=item.sku,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    # Audit log
    AuditService.log_event(
        db=db,
        event_type="ORDER_CREATED",
        entity_type="ORDER",
        entity_id=order.id,
        actor_id="system",
        details={
            "customer_name": order.customer_name,
            "grand_total": str(order.grand_total),
            "currency": order.currency,
        },
    )

    return order


@router.get("", response_model=List[OrderResponse], summary="List Approved Orders")
def list_orders(db: Session = Depends(get_db)):
    """Returns all registered approved orders."""
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse, summary="Get Approved Order Details")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Retrieves an approved order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )
    return order

