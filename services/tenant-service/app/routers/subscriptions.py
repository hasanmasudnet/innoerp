"""
Subscription API routes
"""
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from shared.database.base import get_db
from app.models import (
    OrganizationSubscriptionResponse,
    SubscriptionListFilters,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse
)
from app.services import SubscriptionService, SubscriptionPlanService
from shared.common.errors import handle_exception

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/organization/{organization_id}", response_model=OrganizationSubscriptionResponse)
def get_subscription(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get organization subscription"""
    try:
        subscription = SubscriptionService.get_subscription(db, organization_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        return subscription
    except Exception as e:
        raise handle_exception(e)


@router.get("", response_model=List[OrganizationSubscriptionResponse])
def list_subscriptions(
    status: Optional[str] = Query(None),
    plan_id: Optional[UUID] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all subscriptions with filters"""
    try:
        return SubscriptionService.list_subscriptions(
            db, status=status, plan_id=plan_id, organization_id=organization_id,
            skip=skip, limit=limit
        )
    except Exception as e:
        raise handle_exception(e)


@router.get("/{subscription_id}", response_model=OrganizationSubscriptionResponse)
def get_subscription_by_id(
    subscription_id: UUID,
    db: Session = Depends(get_db)
):
    """Get subscription by ID"""
    try:
        subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        return subscription
    except Exception as e:
        raise handle_exception(e)


# Subscription Plans endpoints
@router.post("/plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    db: Session = Depends(get_db)
):
    """Create new subscription plan"""
    try:
        return SubscriptionPlanService.create_plan(db, plan_data)
    except Exception as e:
        raise handle_exception(e)


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
def list_subscription_plans(
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List all subscription plans"""
    try:
        return SubscriptionPlanService.list_plans(db, active_only=active_only)
    except Exception as e:
        raise handle_exception(e)


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(
    plan_id: UUID,
    db: Session = Depends(get_db)
):
    """Get subscription plan by ID"""
    try:
        plan = SubscriptionPlanService.get_plan(db, plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )
        return plan
    except Exception as e:
        raise handle_exception(e)


@router.patch("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    plan_id: UUID,
    plan_data: SubscriptionPlanUpdate,
    db: Session = Depends(get_db)
):
    """Update subscription plan"""
    try:
        update_dict = plan_data.dict(exclude_unset=True)
        return SubscriptionPlanService.update_plan(db, plan_id, update_dict)
    except Exception as e:
        raise handle_exception(e)


# Placeholder endpoints for orders and payments (would need database tables)
@router.get("/orders")
def get_subscription_orders(
    organization_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get subscription order history"""
    # TODO: Implement when subscription_orders table exists
    return []


@router.get("/payments")
def get_payment_transactions(
    organization_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get payment transaction history"""
    # TODO: Implement when payment_transactions table exists
    return []

