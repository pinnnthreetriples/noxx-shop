import httpx
import logging
from typing import Any, List

from .config import INTERNAL_API_URL, INTERNAL_API_SECRET

logger = logging.getLogger(__name__)


class InternalAPIClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def start(self):
        self._client = httpx.AsyncClient(
            base_url=INTERNAL_API_URL,
            timeout=httpx.Timeout(15.0, connect=10.0),
            headers={"X-Internal-Secret": INTERNAL_API_SECRET},
        )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("InternalAPIClient not started")
        return self._client

    async def pre_checkout(self, invoice_payload: str, total_amount: int) -> dict:
        resp = await self.client.post("/internal/telegram/pre-checkout", json={
            "invoice_payload": invoice_payload,
            "total_amount": total_amount,
            "currency": "XTR",
        })
        resp.raise_for_status()
        return resp.json()

    async def successful_payment(
        self,
        *,
        invoice_payload: str,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
        total_amount: int,
    ) -> dict:
        resp = await self.client.post("/internal/telegram/successful-payment", json={
            "invoice_payload": invoice_payload,
            "telegram_payment_charge_id": telegram_payment_charge_id,
            "provider_payment_charge_id": provider_payment_charge_id,
            "total_amount": total_amount,
            "currency": "XTR",
        })
        resp.raise_for_status()
        return resp.json()

    async def admin_reply(
        self,
        *,
        admin_telegram_id: int,
        reply_to_message_id: int,
        text: str | None,
        file_url: str | None,
        file_type: str | None,
    ) -> dict:
        resp = await self.client.post("/internal/support/admin-reply", json={
            "admin_telegram_id": admin_telegram_id,
            "reply_to_message_id": reply_to_message_id,
            "text": text,
            "file_url": file_url,
            "file_type": file_type,
        })
        resp.raise_for_status()
        return resp.json()

    async def record_admin_message_map(
        self,
        *,
        admin_message_id: int,
        chat_id: int,
        ticket_id: int,
    ) -> dict:
        resp = await self.client.post("/internal/bot/admin-message-map", json={
            "admin_message_id": admin_message_id,
            "chat_id": chat_id,
            "ticket_id": ticket_id,
        })
        resp.raise_for_status()
        return resp.json()

    async def notification_send_result(
        self,
        *,
        notification_id: int,
        user_telegram_id: int,
        status: str,
        error: str | None = None,
    ) -> dict:
        resp = await self.client.post("/internal/notifications/send-result", json={
            "notification_id": notification_id,
            "user_telegram_id": user_telegram_id,
            "status": status,
            "error": error,
        })
        resp.raise_for_status()
        return resp.json()

    async def fetch_unnotified_tickets(self, after_id: int = 0, limit: int = 50) -> dict:
        resp = await self.client.get("/internal/support/tickets/unnotified", params={"after_id": after_id, "limit": limit})
        resp.raise_for_status()
        return resp.json()

    async def pop_notification(self) -> dict:
        resp = await self.client.post("/internal/notifications/pop")
        resp.raise_for_status()
        return resp.json()

    async def pop_delivery(self) -> dict:
        resp = await self.client.post("/internal/bot/deliveries/pop")
        resp.raise_for_status()
        return resp.json()

    async def mark_ticket_notified(self, ticket_id: int) -> dict:
        resp = await self.client.post(f"/internal/support/tickets/{ticket_id}/mark-notified")
        resp.raise_for_status()
        return resp.json()

    async def get_active_admin_telegram_ids(self) -> List[int]:
        resp = await self.client.get("/internal/support/admins/active")
        resp.raise_for_status()
        data = resp.json()
        return data.get("admin_telegram_ids", [])

    async def get_notification_recipients(self, notification_id: int) -> List[int]:
        resp = await self.client.get(f"/internal/notifications/{notification_id}/recipients")
        resp.raise_for_status()
        data = resp.json()
        return data.get("user_telegram_ids", [])


api_client = InternalAPIClient()
