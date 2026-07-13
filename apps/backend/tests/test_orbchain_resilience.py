"""OrbChain payment check resilience (Sentry: httpx transport errors reaching
/orders/{id}/check-payment as unhandled 500s).

Transient network failures — ConnectTimeout, ConnectError, ReadTimeout,
RemoteProtocolError — must degrade to a "still pending, retry later" answer, never
a raised 500. All four are httpx.HTTPError subclasses, which the client already
catches; these tests lock that in end-to-end."""
from types import SimpleNamespace

import httpx
import pytest

import app.modules.payments_orbchain.client as orb_client
from app.core.config import settings
from app.modules.orders.service import OrderService
from app.modules.payments_orbchain.client import OrbChainError, get_payment

_TRANSPORT_ERRORS = [
    httpx.ConnectTimeout("boom"),
    httpx.ConnectError("boom"),
    httpx.ReadTimeout("boom"),
    httpx.RemoteProtocolError("boom"),
]


class _RaisingClient:
    """Stand-in httpx.AsyncClient whose every request raises a transport error."""

    def __init__(self, exc):
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, *_a, **_k):
        raise self._exc

    async def post(self, *_a, **_k):
        raise self._exc


@pytest.mark.parametrize("exc", _TRANSPORT_ERRORS, ids=lambda e: type(e).__name__)
async def test_get_payment_wraps_transport_errors(monkeypatch, exc):
    monkeypatch.setattr(settings, "orbchain_api_key", "k")
    monkeypatch.setattr(orb_client.httpx, "AsyncClient", lambda *a, **k: _RaisingClient(exc))
    with pytest.raises(OrbChainError):
        await get_payment("trk_1")


@pytest.mark.parametrize("exc", _TRANSPORT_ERRORS, ids=lambda e: type(e).__name__)
async def test_check_payment_pending_on_network_error(db_session, monkeypatch, exc):
    monkeypatch.setattr(settings, "orbchain_api_key", "k")
    monkeypatch.setattr(orb_client.httpx, "AsyncClient", lambda *a, **k: _RaisingClient(exc))

    svc = OrderService(db_session)
    order = SimpleNamespace(id=1, status=SimpleNamespace(value="pending"), orbchain_track_id="trk_1")

    async def _order(*_a, **_k):
        return order

    monkeypatch.setattr(svc.order_repo, "get_by_id_for_user", _order)

    result = await svc.check_orbchain_payment(SimpleNamespace(id=1), 1)
    assert result == {"paid": False, "status": "unavailable"}
