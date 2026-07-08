from datetime import datetime
from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field


class PreCheckoutRequest(BaseModel):
    invoice_payload: str
    total_amount: int
    currency: str = "XTR"


class PreCheckoutResponse(BaseModel):
    ok: bool
    order_id: Optional[int] = None
    error_message: Optional[str] = None


class SuccessfulPaymentRequest(BaseModel):
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    total_amount: int
    currency: str = "XTR"


class SuccessfulPaymentResponse(BaseModel):
    ok: bool
    order_id: Optional[int] = None
    user_telegram_id: Optional[int] = None
    message_text: Optional[str] = None
    channel_id: Optional[str] = None
    videos: List[int] = []
    error: Optional[str] = None


class AdminReplyRequest(BaseModel):
    admin_telegram_id: int
    reply_to_message_id: int
    text: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None  # "photo" | "document"


class AdminReplyResponse(BaseModel):
    ok: bool
    ticket_id: Optional[int] = None
    user_telegram_id: Optional[int] = None
    text: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    error: Optional[str] = None


class NotificationSendResultRequest(BaseModel):
    notification_id: int
    user_telegram_id: int
    status: Literal["sent", "failed"]
    error: Optional[str] = None


class NotificationSendResultResponse(BaseModel):
    ok: bool


class TicketNotification(BaseModel):
    ticket_id: int
    user_telegram_id: int
    topic: str
    created_at: datetime
    message: Optional[str] = None


class UnnotifiedTicketsResponse(BaseModel):
    tickets: List[TicketNotification]


class ActiveAdminIdsResponse(BaseModel):
    admin_telegram_ids: List[int]


class NotificationRecipientItem(BaseModel):
    telegram_id: int
    lang: str = "en"


class NotificationRecipientsResponse(BaseModel):
    recipients: List[NotificationRecipientItem]
    product_slug: Optional[str] = None
    titles: Dict[str, str] = Field(default_factory=dict)


class PopNotificationResponse(BaseModel):
    empty: bool = True
    notification_id: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    product_id: Optional[int] = None
    webapp_url: Optional[str] = None


class AdminMessageMapRequest(BaseModel):
    admin_message_id: int
    chat_id: int
    ticket_id: int


class AdminMessageMapResponse(BaseModel):
    ok: bool


class MarkTicketNotifiedResponse(BaseModel):
    ok: bool