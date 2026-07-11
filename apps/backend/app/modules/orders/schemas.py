from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemOut(BaseModel):
    id: int
    product_id: int
    title: str
    quantity: int
    price_stars: int
    model_config = ConfigDict(from_attributes=True)


class CartOut(BaseModel):
    items: List[CartItemOut]
    total_stars: int
    item_count: int
    promo_code: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CartEstimateIn(BaseModel):
    product_ids: List[int]
    promo_code: Optional[str] = None


class CartEstimateOut(BaseModel):
    product_ids: List[int]
    total_stars: int
    base_discount_percent: int
    promo_discount_percent: int
    final_discount_percent: int
    to_pay_stars: int
    approx_usd: Optional[float] = None
    promo_code: Optional[str] = None


class CheckoutIn(BaseModel):
    product_ids: List[int]
    promo_code: Optional[str] = None
    provider: Optional[str] = None  # "telegram" (Stars) | "orbchain" (crypto); None = server default


class SubscriptionCheckoutIn(BaseModel):
    plan: Literal["week", "month", "year"]
    provider: Optional[str] = None


class ClaimIn(BaseModel):
    product_id: int


class CheckoutOut(BaseModel):
    order_id: int
    invoice_url: str
    provider: str = "telegram"  # "orbchain" (in-app crypto) or "telegram" (Stars)
    amount_usd: Optional[float] = None


class CoinOut(BaseModel):
    code: str
    ticker: str
    name: str
    network: str
    color: str


class SelectCoinIn(BaseModel):
    coin: str


class PaymentStateOut(BaseModel):
    order_id: int
    status: str  # order status: "pending" | "paid" | "unavailable"
    paid: bool
    amount_usd: float
    pay_currency: Optional[str] = None
    pay_amount: Optional[str] = None
    address: Optional[str] = None
    qr: Optional[str] = None  # SVG data URI of the address (empty until a coin is picked)
    expires_at: Optional[int] = None
    coins: List[CoinOut] = []


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    title: str
    quantity: int
    price_stars: int
    google_drive_link: Optional[str] = None
    tg_delivered: bool = False
    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    status: str
    total_stars: int
    base_discount_percent: int
    promo_discount_percent: int
    final_discount_percent: int
    paid_stars: int
    approx_usd: Optional[float] = None
    subscription_plan: Optional[str] = None
    created_at: datetime
    items: List[OrderItemOut]
    model_config = ConfigDict(from_attributes=True)


class ReceiptOut(BaseModel):
    order_id: int
    date: datetime
    videos: List[OrderItemOut]
    total_stars: int
    base_discount_percent: int
    promo_discount_percent: int
    final_discount_percent: int
    paid_stars: int
    approx_usd: Optional[float] = None
    download_links: List[str]
    model_config = ConfigDict(from_attributes=True)
