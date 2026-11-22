"""REQ-BE-090..097: AI call records, debug log, model prices and costs.

Gemini is faked at the HTTP level (requests.post), so recording and retries run for real.
"""

import json
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
import requests

from app.database import SessionLocal
from app.models import AiCall
from app.services import ai_buddy, ai_monitoring

KEY = "AIza-monitoring-secret-9876"


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str | None = None):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else json.dumps(payload)

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def answer(text=None, call=None, usage=None) -> FakeResponse:
    parts = []
    if text is not None:
        parts.append({"text": text})
    if call is not None:
        parts.append({"functionCall": {"name": call[0], "args": call[1]}})
    payload = {"candidates": [{"content": {"role": "model", "parts": parts}}]}
    if usage is not None:
        payload["usageMetadata"] = usage
    return FakeResponse(200, payload)


class FakeHttp:
    """Scripted Gemini HTTP answers; an exception in the script is raised instead."""

    def __init__(self, monkeypatch):
        self.script: list = []
        self.sent: list[dict] = []
        monkeypatch.setattr(ai_buddy.requests, "post", self._post)
        monkeypatch.setattr(ai_buddy, "_sleep", lambda _seconds: None)

    def _post(self, url, json=None, headers=None, timeout=None):
        self.sent.append({"url": url, "json": json, "headers": headers})
        item = self.script.pop(0) if self.script else answer("klaar")
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def http(monkeypatch):
    return FakeHttp(monkeypatch)


def set_config(client, admin_headers, **fields):
    response = client.put("/api/admin/ai/config", headers=admin_headers, json=fields)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def configured(client, admin_headers):
    set_config(client, admin_headers, api_key=KEY, model="gemini-mon", enabled=True, debug_log_enabled=False)
    yield
    set_config(
        client,
        admin_headers,
        clear_api_key=True,
        model="",
        enabled=False,
        debug_log_enabled=False,
        debug_retention_days=7,
    )


def calls_of(person_id: int) -> list[AiCall]:
    db = SessionLocal()
    try:
        return db.query(AiCall).filter(AiCall.person_id == person_id).order_by(AiCall.id).all()
    finally:
        db.close()


def send(client, headers, text):
    return client.post("/api/ai/messages", headers=headers, json={"text": text})


def add_call(**fields) -> int:
    db = SessionLocal()
    try:
        call = AiCall(
            **{
                "activity": "chat",
                "model": "gemini-mon",
                "status": "ok",
                "prompt_tokens": 0,
                "output_tokens": 0,
                "thinking_tokens": 0,
                "cached_tokens": 0,
                **fields,
            }
        )
        db.add(call)
        db.commit()
        return call.id
    finally:
        db.close()


def add_price(client, admin_headers, model, inp, out, valid_from):
    response = client.post(
        "/api/admin/ai/prices",
        headers=admin_headers,
        json={"model": model, "input_price_per_1m": inp, "output_price_per_1m": out, "valid_from": valid_from},
    )
    assert response.status_code == 201, response.text
    return response.json()


def utc(local_iso: str) -> datetime:
    """A naive UTC datetime for an Europe/Amsterdam wall clock time."""
    local = datetime.fromisoformat(local_iso).replace(tzinfo=ai_monitoring.TZ)
    return local.astimezone(UTC).replace(tzinfo=None)


# --- access (REQ-BE-090) ------------------------------------------------------------------------


def test_monitoring_endpoints_are_admin_only(client, admin_headers, make_user):
    _person, headers = make_user("Nieuwsgierig")
    for method, path in [
        ("get", "/api/admin/ai/calls"),
        ("get", "/api/admin/ai/calls/1"),
        ("delete", "/api/admin/ai/calls/content"),
        ("get", "/api/admin/ai/prices"),
        ("post", "/api/admin/ai/prices"),
        ("delete", "/api/admin/ai/prices/1"),
        ("get", "/api/admin/ai/costs"),
    ]:
        assert getattr(client, method)(path, headers=headers).status_code == 403, path
    assert client.get("/api/admin/ai/calls", headers=admin_headers).status_code == 200
    assert client.get("/api/admin/ai/costs", headers=admin_headers).status_code == 200


# --- recording (REQ-BE-091) ---------------------------------------------------------------------


def test_each_round_is_recorded_with_tokens(client, make_user, configured, http):
    person, headers = make_user("Rondes")
    today = date.today().isoformat()
    search = ("search_tasks", {"start_date": today, "end_date": today})
    usage = {
        "promptTokenCount": 100,
        "candidatesTokenCount": 20,
        "thoughtsTokenCount": 30,
        "cachedContentTokenCount": 40,
    }
    http.script = [answer(call=search, usage=usage), answer(call=search, usage=usage), answer("Klaar", usage=usage)]
    response = send(client, headers, "Zoek twee keer")
    assert response.status_code == 200, response.text

    calls = calls_of(person["id"])
    assert len(calls) == 3
    assert {c.message_id for c in calls} == {response.json()["user_message"]["id"]}
    assert all(c.status == "ok" and c.http_status == 200 and c.activity == "chat" for c in calls)
    assert [(c.prompt_tokens, c.output_tokens, c.thinking_tokens, c.cached_tokens) for c in calls] == [
        (100, 20, 30, 40)
    ] * 3
    assert all(c.model == "gemini-mon" and c.duration_ms is not None for c in calls)


def test_failed_call_is_recorded(client, make_user, configured, http):
    person, headers = make_user("Fouten")
    # A 4xx is not retried (REQ-BE-083).
    http.script = [FakeResponse(400, {"error": {"message": "API key not valid"}})]
    assert send(client, headers, "Hoi").status_code == 502
    # A timeout is retried twice, each attempt recorded.
    http.script = [requests.Timeout("read timeout")] * 3
    assert send(client, headers, "Nog eens").status_code == 502

    calls = calls_of(person["id"])
    assert [(c.status, c.http_status) for c in calls] == [("error", 400)] + [("error", None)] * 3
    assert "API key not valid" in calls[0].error_message
    assert "read timeout" in calls[1].error_message


def test_empty_answer_is_recorded(client, make_user, configured, http):
    person, headers = make_user("Leeg")
    http.script = [FakeResponse(200, {"candidates": [{"content": {"parts": []}, "finishReason": "SAFETY"}]})]
    response = send(client, headers, "Iets geks")
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == ai_buddy.EMPTY_REPLY
    assert [c.status for c in calls_of(person["id"])] == ["empty"]


def test_log_failure_does_not_break_chat(client, make_user, configured, http, monkeypatch):
    person, headers = make_user("Logfout")

    class BrokenSession:
        def add(self, _obj):
            raise RuntimeError("disk full")

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(ai_monitoring, "SessionLocal", BrokenSession)
    http.script = [answer("Gewoon antwoord")]
    response = send(client, headers, "Hoi")
    assert response.status_code == 200
    assert response.json()["reply"]["text"] == "Gewoon antwoord"
    assert calls_of(person["id"]) == []


# --- debug log (REQ-BE-092, REQ-BE-093) -----------------------------------------------------------


def test_no_content_while_debug_off(client, make_user, configured, http):
    person, headers = make_user("Stil")
    http.script = [answer("Hoi")]
    send(client, headers, "Geheim bericht")
    (call,) = calls_of(person["id"])
    assert call.request_body is None and call.response_body is None


def test_full_content_while_debug_on(client, admin_headers, make_user, configured, http):
    person, headers = make_user("Open")
    set_config(client, admin_headers, debug_log_enabled=True)
    http.script = [answer("Zichtbaar antwoord")]
    send(client, headers, "Zichtbaar bericht")
    (call,) = calls_of(person["id"])
    request = json.loads(call.request_body)
    assert request["contents"][-1]["parts"][0]["text"] == "Zichtbaar bericht"
    assert request["systemInstruction"]["parts"][0]["text"] == ai_buddy.DEFAULT_SYSTEM_PROMPT
    assert request["tools"][0]["functionDeclarations"]
    assert "Zichtbaar antwoord" in call.response_body


def test_api_key_is_never_stored(client, admin_headers, make_user, configured, http):
    person, headers = make_user("Sleutel")
    set_config(client, admin_headers, debug_log_enabled=True)
    http.script = [FakeResponse(403, {"error": {"message": "denied"}}), answer("ok")]
    send(client, headers, "Een")
    send(client, headers, "Twee")
    for call in calls_of(person["id"]):
        assert KEY not in (call.request_body or "") + (call.response_body or "") + (call.error_message or "")
    assert http.sent[0]["headers"]["x-goog-api-key"] == KEY  # it does go to Google, in a header


def test_retention_removes_old_content(client, admin_headers, configured):
    set_config(client, admin_headers, debug_retention_days=3)
    old = add_call(
        created_at=datetime.now(UTC) - timedelta(days=4), request_body="{}", response_body="{}", prompt_tokens=5
    )
    new = add_call(created_at=datetime.now(UTC) - timedelta(days=2), request_body="{}", response_body="{}")
    db = SessionLocal()
    try:
        ai_monitoring.purge_old_content(db)
        old_call, new_call = db.get(AiCall, old), db.get(AiCall, new)
        assert old_call.request_body is None and old_call.response_body is None and old_call.prompt_tokens == 5
        assert new_call.request_body == "{}"
    finally:
        db.close()
    assert (
        client.put("/api/admin/ai/config", headers=admin_headers, json={"debug_retention_days": 91}).status_code == 400
    )


def test_admin_clears_all_content(client, admin_headers):
    call_id = add_call(created_at=datetime.now(UTC), request_body="{}", response_body="{}", prompt_tokens=7)
    response = client.delete("/api/admin/ai/calls/content", headers=admin_headers)
    assert response.status_code == 200 and response.json()["cleared"] >= 1
    db = SessionLocal()
    try:
        call = db.get(AiCall, call_id)
        assert call.request_body is None and call.prompt_tokens == 7
    finally:
        db.close()


def test_clearing_conversation_removes_own_content(client, make_user):
    me, headers = make_user("Wisser")
    other, _ = make_user("Blijver")
    mine = add_call(person_id=me["id"], request_body="{}", response_body="{}")
    theirs = add_call(person_id=other["id"], request_body="{}", response_body="{}")
    assert client.delete("/api/ai/messages", headers=headers).status_code == 200
    db = SessionLocal()
    try:
        assert db.get(AiCall, mine).request_body is None
        assert db.get(AiCall, theirs).request_body == "{}"
    finally:
        db.close()


def test_deleting_person_keeps_costs(client, admin_headers, make_user):
    person, _ = make_user("Vertrekker")
    call_id = add_call(person_id=person["id"], request_body="{}", response_body="{}", prompt_tokens=11)
    assert client.delete(f"/api/admin/users/{person['id']}", headers=admin_headers).status_code == 200
    db = SessionLocal()
    try:
        call = db.get(AiCall, call_id)
        assert call.person_id is None and call.request_body is None and call.prompt_tokens == 11
    finally:
        db.close()


# --- call log (REQ-BE-094) ----------------------------------------------------------------------


def test_call_log_paging_and_filters(client, admin_headers, make_user):
    person, _ = make_user("Veel")
    pid = person["id"]
    base = datetime(2021, 6, 15, 10, 0)
    ids = [add_call(person_id=pid, created_at=base + timedelta(minutes=i), message_id=None) for i in range(55)]
    add_call(person_id=pid, created_at=base, status="error", activity="test-activity")

    page1 = client.get(f"/api/admin/ai/calls?person_id={pid}", headers=admin_headers).json()
    assert page1["total"] == 56 and len(page1["items"]) == 50 and page1["page_size"] == 50
    assert page1["items"][0]["id"] > page1["items"][1]["id"]  # newest first
    page2 = client.get(f"/api/admin/ai/calls?person_id={pid}&page=2", headers=admin_headers).json()
    assert len(page2["items"]) == 6

    def total(query):
        return client.get(f"/api/admin/ai/calls?person_id={pid}&{query}", headers=admin_headers).json()["total"]

    assert total("status=error") == 1
    assert total("activity=test-activity") == 1
    assert total("date_from=2021-06-15&date_to=2021-06-15") == 56
    assert total("date_from=2021-06-16") == 0
    assert client.get("/api/admin/ai/calls?status=weird", headers=admin_headers).status_code == 400
    assert ids  # rows exist


def test_call_log_detail_with_content(client, admin_headers, make_user, configured, http):
    person, headers = make_user("Detail")
    set_config(client, admin_headers, debug_log_enabled=True)
    today = date.today().isoformat()
    http.script = [answer(call=("search_tasks", {"start_date": today, "end_date": today})), answer("Klaar")]
    message_id = send(client, headers, "Zoek").json()["user_message"]["id"]

    listing = client.get(f"/api/admin/ai/calls?message_id={message_id}", headers=admin_headers).json()
    assert listing["total"] == 2 and all(i["has_content"] for i in listing["items"])
    detail = client.get(f"/api/admin/ai/calls/{listing['items'][0]['id']}", headers=admin_headers).json()
    assert detail["person"]["id"] == person["id"]
    assert detail["request"]["contents"][0]["parts"][0]["text"] == "Zoek"
    assert detail["response"]["candidates"][0]["content"]["parts"][0]["text"] == "Klaar"
    assert client.get("/api/admin/ai/calls/999999", headers=admin_headers).status_code == 404


# --- prices and costs (REQ-BE-095, REQ-BE-096, REQ-BE-097) -----------------------------------------


def test_price_history_per_model(client, admin_headers):
    model = f"gemini-prijs-{uuid.uuid4().hex[:6]}"
    old = add_price(client, admin_headers, model, 0.10, 0.40, "2024-01-01")
    add_price(client, admin_headers, model, 0.30, 2.50, "2025-01-01")
    entry = next(m for m in client.get("/api/admin/ai/prices", headers=admin_headers).json() if m["model"] == model)
    assert [p["valid_from"] for p in entry["prices"]] == ["2025-01-01", "2024-01-01"]
    assert entry["current_price"]["input_price_per_1m"] == 0.30

    assert client.delete(f"/api/admin/ai/prices/{old['id']}", headers=admin_headers).status_code == 200
    entry = next(m for m in client.get("/api/admin/ai/prices", headers=admin_headers).json() if m["model"] == model)
    assert [p["valid_from"] for p in entry["prices"]] == ["2025-01-01"]
    bad = {"model": model, "input_price_per_1m": -1, "output_price_per_1m": 1, "valid_from": "2025-01-01"}
    assert client.post("/api/admin/ai/prices", headers=admin_headers, json=bad).status_code == 422


def test_models_without_price_are_listed(client, admin_headers, configured):
    logged = f"gemini-gelogd-{uuid.uuid4().hex[:6]}"
    add_call(model=logged)
    models = {m["model"]: m for m in client.get("/api/admin/ai/prices", headers=admin_headers).json()}
    assert models[logged]["logged"] and not models[logged]["has_price"]
    assert models["gemini-mon"]["configured"] and not models["gemini-mon"]["has_price"]


def test_cost_uses_price_of_call_day(client, admin_headers):
    model = f"gemini-dag-{uuid.uuid4().hex[:6]}"
    add_price(client, admin_headers, model, 1.0, 0.0, "2022-03-01")
    add_price(client, admin_headers, model, 2.0, 0.0, "2022-03-10")
    # 23:30 on 9 March in Amsterdam is still the old price, 00:30 on 10 March the new one.
    add_call(model=model, prompt_tokens=1_000_000, created_at=utc("2022-03-09T23:30:00"))
    add_call(model=model, prompt_tokens=1_000_000, created_at=utc("2022-03-10T00:30:00"))
    report = client.get("/api/admin/ai/costs?date_from=2022-03-09&date_to=2022-03-10", headers=admin_headers).json()
    days = {d["date"]: d["cost_eur"] for d in report["by_day"]}
    assert days["2022-03-09"] == pytest.approx(1.0)
    assert days["2022-03-10"] == pytest.approx(2.0)


def test_thinking_tokens_cost_as_output(client, admin_headers):
    model = f"gemini-denk-{uuid.uuid4().hex[:6]}"
    add_price(client, admin_headers, model, 1.0, 10.0, "2022-04-01")
    add_call(
        model=model,
        prompt_tokens=100_000,
        output_tokens=50_000,
        thinking_tokens=150_000,
        created_at=utc("2022-04-05T12:00:00"),
    )
    report = client.get("/api/admin/ai/costs?date_from=2022-04-05&date_to=2022-04-05", headers=admin_headers).json()
    entry = next(m for m in report["by_model"] if m["model"] == model)
    assert entry["cost_eur"] == pytest.approx(0.1 + 2.0)


def test_unpriced_calls_are_counted(client, admin_headers):
    model = f"gemini-zonder-{uuid.uuid4().hex[:6]}"
    add_call(model=model, prompt_tokens=500, created_at=utc("2022-05-05T12:00:00"))
    report = client.get("/api/admin/ai/costs?date_from=2022-05-05&date_to=2022-05-05", headers=admin_headers).json()
    entry = next(m for m in report["by_model"] if m["model"] == model)
    assert entry["cost_eur"] == 0 and entry["unpriced_calls"] == 1
    assert report["summary"]["unpriced_calls"] >= 1


def test_cost_overview_totals_and_breakdowns(client, admin_headers, make_user):
    a, _ = make_user("KostenA")
    b, _ = make_user("KostenB")
    model = f"gemini-totaal-{uuid.uuid4().hex[:6]}"
    add_price(client, admin_headers, model, 1.0, 2.0, "2019-01-01")
    add_call(person_id=a["id"], model=model, prompt_tokens=1_000_000, created_at=utc("2019-02-01T10:00:00"))
    add_call(person_id=a["id"], model=model, output_tokens=1_000_000, created_at=utc("2019-02-02T10:00:00"))
    add_call(
        person_id=b["id"], model=model, activity="other", prompt_tokens=1_000_000, created_at=utc("2019-02-02T11:00:00")
    )

    report = client.get("/api/admin/ai/costs?date_from=2019-02-01&date_to=2019-02-03", headers=admin_headers).json()
    s = report["summary"]
    assert (s["calls"], s["prompt_tokens"], s["output_tokens"]) == (3, 2_000_000, 1_000_000)
    assert s["cost_eur"] == pytest.approx(4.0)
    assert s["active_users"] == 2 and s["avg_cost_per_user"] == pytest.approx(2.0)
    users = {u["person_id"]: u for u in report["by_user"]}
    assert users[a["id"]]["cost_eur"] == pytest.approx(3.0) and users[b["id"]]["calls"] == 1
    assert {x["activity"]: x["calls"] for x in report["by_activity"]} == {"chat": 2, "other": 1}
    assert report["by_model"][0]["current_price"]["output_price_per_1m"] == 2.0
    assert [(d["date"], d["calls"]) for d in report["by_day"]] == [
        ("2019-02-01", 1),
        ("2019-02-02", 2),
        ("2019-02-03", 0),
    ]
    bad = client.get("/api/admin/ai/costs?date_from=2019-02-03&date_to=2019-02-01", headers=admin_headers)
    assert bad.status_code == 400


def test_cost_overview_defaults_to_current_month(client, admin_headers):
    report = client.get("/api/admin/ai/costs", headers=admin_headers).json()
    today = ai_monitoring.today_local()
    first = today.replace(day=1)
    last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    assert report["period"] == {"from": first.isoformat(), "to": last.isoformat()}
    assert len(report["by_day"]) == last.day
