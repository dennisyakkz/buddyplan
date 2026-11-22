"""REQ-BE-080..089: the AI buddy. Gemini is replaced by a scripted fake; tools run for real."""

from datetime import date, datetime, timedelta

import pytest

from app.database import SessionLocal
from app.models import AgendaItem, Person
from app.services import ai_buddy
from app.services.dashboard_service import PersonService

DAY = date.today() + timedelta(days=2)


class FakeGemini:
    """Plays back scripted model turns and records what the backend sent."""

    def __init__(self, monkeypatch):
        self.turns: list = []
        self.requests: list[dict] = []
        monkeypatch.setattr(ai_buddy, "generate", self._generate)

    def reply(self, text: str):
        self.turns.append({"role": "model", "parts": [{"text": text}]})
        return self

    def call(self, name: str, **args):
        self.turns.append({"role": "model", "parts": [{"functionCall": {"name": name, "args": args}}]})
        return self

    def _generate(self, cfg, system, contents, *, allow_tools, log=None):
        self.requests.append({"system": list(system), "contents": list(contents), "allow_tools": allow_tools})
        if not self.turns:
            return {"role": "model", "parts": [{"text": "klaar"}]}
        return self.turns.pop(0)

    def tool_results(self) -> list[dict]:
        """All functionResponse payloads the backend sent back, in order."""
        last = self.requests[-1]["contents"]
        return [
            part["functionResponse"]["response"]
            for content in last
            for part in content["parts"]
            if "functionResponse" in part
        ]


@pytest.fixture
def configured(client, admin_headers):
    response = client.put(
        "/api/admin/ai/config",
        headers=admin_headers,
        json={"api_key": "AIza-test-key-1234", "model": "gemini-test", "system_prompt": "", "enabled": True},
    )
    assert response.status_code == 200, response.text
    yield
    client.put(
        "/api/admin/ai/config",
        headers=admin_headers,
        json={"clear_api_key": True, "model": "", "thinking_level": "", "enabled": False, "context_messages": 20},
    )


@pytest.fixture
def gemini(monkeypatch):
    return FakeGemini(monkeypatch)


def send(client, headers, text):
    return client.post("/api/ai/messages", headers=headers, json={"text": text})


def agenda_titles(person_id: int) -> set[str]:
    db = SessionLocal()
    try:
        return {i.title for i in db.query(AgendaItem).filter(AgendaItem.person_id == person_id)}
    finally:
        db.close()


# --- settings (REQ-BE-081, REQ-BE-082, REQ-BE-083) -------------------------------------------------


def test_unavailable_until_configured(client, admin_headers, make_user):
    _person, headers = make_user("Leeg")
    client.put("/api/admin/ai/config", headers=admin_headers, json={"clear_api_key": True, "model": ""})
    assert client.get("/api/ai/status", headers=headers).json() == {"configured": False}
    response = send(client, headers, "Hoi")
    assert response.status_code == 503
    assert response.json()["detail"] == "De AI buddy is nog niet ingesteld door de beheerder."


def test_admin_sets_key_model_and_prompt(client, admin_headers, make_user, configured):
    _person, headers = make_user("Gewoon")
    assert client.get("/api/ai/status", headers=headers).json() == {"configured": True}
    assert client.get("/api/admin/ai/config", headers=headers).status_code == 403

    cfg = client.get("/api/admin/ai/config", headers=admin_headers).json()
    assert cfg["has_api_key"] and cfg["api_key_hint"] == "…1234"
    assert "AIza-test-key-1234" not in str(cfg)
    assert cfg["model"] == "gemini-test"
    assert cfg["is_default_prompt"] and cfg["system_prompt"] == ai_buddy.DEFAULT_SYSTEM_PROMPT

    # An empty key keeps the stored one; a custom prompt is kept until restored.
    cfg = client.put(
        "/api/admin/ai/config", headers=admin_headers, json={"api_key": "", "system_prompt": "Wees kort."}
    ).json()
    assert cfg["api_key_hint"] == "…1234"
    assert cfg["system_prompt"] == "Wees kort." and not cfg["is_default_prompt"]
    cfg = client.put("/api/admin/ai/config", headers=admin_headers, json={"system_prompt": ""}).json()
    assert cfg["is_default_prompt"]


def test_context_is_always_sent(client, admin_headers, make_user, configured, gemini):
    person, headers = make_user("Sam")
    client.put("/api/admin/ai/config", headers=admin_headers, json={"system_prompt": "Alleen dit."})
    gemini.reply("Hallo!")
    response = send(client, headers, "Hoi")
    assert response.status_code == 200, response.text
    assert response.json()["reply"]["text"] == "Hallo!"

    prompt, context = gemini.requests[0]["system"]
    assert prompt == "Alleen dit."
    assert date.today().isoformat() in context
    assert person["name"] in context and f"person_id {person['id']}" in context
    assert "Beheerder" in context  # the other people in the planner


def test_context_names_this_week_and_next_week(make_user):
    """'Deze week' on a Sunday was taken as Sunday to Saturday; the context now gives Monday to Sunday (REQ-BE-082)."""
    person, _headers = make_user("Weekje")
    db = SessionLocal()
    try:
        user = db.get(Person, person["id"])
        sunday = datetime(2026, 11, 22, 20, 30, tzinfo=ai_buddy.TZ)
        context = ai_buddy.context_text(db, user, sunday)
        assert "Deze week loopt van maandag 16 november t/m zondag 22 november (2026-11-16 t/m 2026-11-22)" in context
        assert "volgende week van maandag 23 november t/m zondag 29 november (2026-11-23 t/m 2026-11-29)" in context
        wednesday = datetime(2026, 12, 30, 9, 0, tzinfo=ai_buddy.TZ)
        assert "maandag 28 december t/m zondag 3 januari" in ai_buddy.context_text(db, user, wednesday)
    finally:
        db.close()


def test_list_models_keeps_generating_models(monkeypatch):
    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "models": [
                    {"name": "models/gemini-b", "displayName": "B", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/embed", "displayName": "E", "supportedGenerationMethods": ["embedContent"]},
                    {"name": "models/gemini-a", "displayName": "A", "supportedGenerationMethods": ["generateContent"]},
                ]
            }

    monkeypatch.setattr(ai_buddy.requests, "get", lambda *a, **k: Response())
    assert ai_buddy.list_models("key") == [
        {"name": "gemini-a", "display_name": "A"},
        {"name": "gemini-b", "display_name": "B"},
    ]


def test_gemini_failure_keeps_the_message(client, make_user, configured, monkeypatch):
    _person, headers = make_user("Fout")

    def fail(*_args, **_kwargs):
        raise ai_buddy.AiUnavailable("timeout")

    monkeypatch.setattr(ai_buddy, "generate", fail)
    response = send(client, headers, "Wat staat er morgen?")
    assert response.status_code == 502
    assert response.json()["detail"] == "De AI buddy is nu niet bereikbaar. Probeer het later opnieuw."
    response = send(client, headers, "Wat staat er morgen?")  # 'Opnieuw' sends the same text
    messages = client.get("/api/ai/messages", headers=headers).json()
    assert [m["text"] for m in messages] == ["Wat staat er morgen?"]


# --- tools and rights (REQ-BE-084, REQ-BE-085, REQ-BE-089) -----------------------------------------


def test_agenda_tools_create_search_update(client, make_user, configured, gemini):
    person, headers = make_user("Agenda")
    pid = person["id"]
    gemini.call("create_agenda_item", person_id=pid, title="Training", date=DAY.isoformat(), start_time="18:00").reply(
        "Gezet!"
    )
    etag_before = client.get("/api/dashboard/etag", headers=headers).json()["etag"]
    assert send(client, headers, "Zet training erin").status_code == 200
    created = gemini.tool_results()[0]["created"]
    assert created["title"] == "Training" and created["start_time"] == "18:00"
    assert client.get("/api/dashboard/etag", headers=headers).json()["etag"] != etag_before  # REQ-BE-089

    gemini.call(
        "search_agenda", start_date=DAY.isoformat(), end_date=DAY.isoformat(), person_id=pid, keywords=["train"]
    ).call("update_agenda_item", id=created["id"], title="Training JO15", end_time="19:30").reply("Aangepast")
    send(client, headers, "Maak er JO15 van tot half acht")
    search, update = gemini.tool_results()
    assert [i["id"] for i in search["items"]] == [created["id"]]
    assert update["updated"]["title"] == "Training JO15" and update["updated"]["end_time"] == "19:30"
    assert agenda_titles(pid) == {"Training JO15"}


def test_search_results_include_the_weekday(client, make_user, configured, gemini):
    """A small model computing the weekday itself from a bare date gave a wrong day name in production."""
    person, headers = make_user("Weekdag")
    pid = person["id"]
    wednesday = date(2026, 11, 25)
    gemini.call("create_agenda_item", person_id=pid, title="Training", date=wednesday.isoformat()).reply("Gezet!")
    send(client, headers, "Zet training erin")

    gemini.call("search_agenda", start_date=wednesday.isoformat(), end_date=wednesday.isoformat()).reply("Klaar")
    send(client, headers, "Wanneer is de training?")
    search = gemini.tool_results()[-1]
    assert search["items"][0]["weekday"] == "woensdag"


def add_agenda(person_id: int, *items: tuple[str, int]) -> None:
    """Agenda items (title, days after DAY) straight in the database."""
    db = SessionLocal()
    try:
        for title, offset in items:
            db.add(
                AgendaItem(
                    person_id=person_id, title=title, anchor_date=DAY + timedelta(days=offset), repeat_type="once"
                )
            )
        db.commit()
    finally:
        db.close()


def search(client, headers, gemini, person_id, tool="search_agenda", days=1, **args):
    """Runs one search for one person over `days` days from DAY and returns its tool result."""
    end = DAY + timedelta(days=days - 1)
    gemini.call(tool, person_id=person_id, start_date=DAY.isoformat(), end_date=end.isoformat(), **args).reply("Klaar")
    assert send(client, headers, f"Zoek {days} dagen").status_code == 200
    return gemini.tool_results()[-1]


def test_text_filter_ignores_spacing(client, make_user, configured, gemini):
    """A text filter of 'voetbaltraining' missed 'Voetbal training' in production."""
    person, headers = make_user("Zoeker")
    add_agenda(person["id"], ("Voetbal training", 0), ("Tandarts", 1))
    result = search(client, headers, gemini, person["id"], days=20, keywords=["voetbaltraining"])
    assert [i["title"] for i in result["items"]] == ["Voetbal training"]
    assert "note" not in result


def test_short_search_returns_everything(client, make_user, configured, gemini):
    """'trainen' missed 'Voetbaltraining': up to 14 days the model gets everything and judges it (REQ-BE-085)."""
    person, headers = make_user("Kort")
    add_agenda(person["id"], ("Voetbaltraining", 0), ("Voetbal training", 2), ("Tandarts", 13), ("Later", 14))
    result = search(client, headers, gemini, person["id"], days=14, keywords=["trainen"])
    assert [i["title"] for i in result["items"]] == ["Voetbaltraining", "Voetbal training", "Tandarts"]
    assert "note" not in result

    enable_tasks(person["id"])
    gemini.call("create_task", person_id=person["id"], title="Afwas", date=DAY.isoformat()).reply("Ok")
    send(client, headers, "Taak afwas")
    tasks = search(client, headers, gemini, person["id"], tool="search_tasks", days=7, keywords=["stofzuigen"])
    assert [t["title"] for t in tasks["tasks"]] == ["Afwas"]


def test_month_search_falls_back_to_everything(client, make_user, configured, gemini):
    """15 to 31 days: any keyword matches; nothing matching, or no keywords, gives everything with a note."""
    person, headers = make_user("Maand")
    add_agenda(person["id"], ("Voetbaltraining", 0), ("Tandarts", 10), ("Zwemmen", 20), ("Te laat", 31))

    result = search(client, headers, gemini, person["id"], days=31, keywords=["zwem", "TANDARTS"])
    assert [i["title"] for i in result["items"]] == ["Tandarts", "Zwemmen"]
    assert "note" not in result

    result = search(client, headers, gemini, person["id"], days=31, keywords=["trainen"])
    assert [i["title"] for i in result["items"]] == ["Voetbaltraining", "Tandarts", "Zwemmen"]
    assert "Geen titel bevat" in result["note"]

    result = search(client, headers, gemini, person["id"], days=15)
    assert [i["title"] for i in result["items"]] == ["Voetbaltraining", "Tandarts"]
    assert "Geen zoekwoorden" in result["note"]


def test_long_search_needs_keywords(client, make_user, configured, gemini):
    """Over 31 days only with keywords and only matches, no fallback; still at most 180 days."""
    person, headers = make_user("Lang")
    add_agenda(person["id"], ("Voetbaltraining", 0), ("Tandarts", 40))

    assert search(client, headers, gemini, person["id"], days=32) == {
        "error": "Geef zoekwoorden op, of zoek in een periode van maximaal 31 dagen"
    }
    result = search(client, headers, gemini, person["id"], days=60, keywords=["tand"])
    assert [i["title"] for i in result["items"]] == ["Tandarts"]
    result = search(client, headers, gemini, person["id"], days=60, keywords=["trainen"])
    assert result == {"items": []}
    assert search(client, headers, gemini, person["id"], days=182, keywords=["tand"]) == {
        "error": "Datumbereik te groot (max 180 dagen)"
    }


def test_search_rules_are_in_the_tool_descriptions():
    """The range rules live in the fixed tool descriptions, not in the editable prompt (REQ-BE-085)."""
    tools = {t["name"]: t for t in ai_buddy.TOOL_DECLARATIONS}
    for name in ("search_agenda", "search_tasks"):
        description = tools[name]["description"]
        assert "Tot en met 14 dagen" in description and "Langer dan 31 dagen" in description, name
        keywords = tools[name]["parameters"]["properties"]["keywords"]
        assert keywords["type"] == "array" and keywords["items"] == {"type": "string"}
    assert "14 dagen" not in ai_buddy.DEFAULT_SYSTEM_PROMPT


def enable_tasks(person_id: int) -> None:
    """New users have the task system off (REQ-BE-022)."""
    db = SessionLocal()
    try:
        service = PersonService(db)
        service.set_tasks_enabled(person_id, True)
        service.set_task_managers(person_id, [person_id])
        db.commit()
    finally:
        db.close()


def test_task_tools_create_search_update(client, make_user, configured, gemini):
    person, headers = make_user("Taken")
    pid = person["id"]
    enable_tasks(pid)
    gemini.call("create_task", person_id=pid, title="Vaatwasser", date=DAY.isoformat()).reply("Ok")
    send(client, headers, "Taak vaatwasser")
    task = gemini.tool_results()[0]["created"]
    assert task["title"] == "Vaatwasser", gemini.tool_results()

    gemini.call("search_tasks", start_date=DAY.isoformat(), end_date=DAY.isoformat(), person_id=pid).call(
        "update_task", id=task["id"], title="Vaatwasser uitruimen", repeat_type="weekly"
    ).reply("Ok")
    send(client, headers, "Elke week, en uitruimen")
    search, update = gemini.tool_results()
    assert [t["title"] for t in search["tasks"]] == ["Vaatwasser"]
    assert update["updated"]["title"] == "Vaatwasser uitruimen" and update["updated"]["repeat_type"] == "weekly"


def test_tools_have_the_rights_of_the_caller(client, make_user, configured, gemini):
    other, _ = make_user("Ander")
    enable_tasks(other["id"])
    _person, headers = make_user("Beller")
    gemini.call("create_agenda_item", person_id=other["id"], title="Stiekem", date=DAY.isoformat()).call(
        "create_task", person_id=other["id"], title="Stiekem", date=DAY.isoformat()
    ).reply("Dat mag niet")
    assert send(client, headers, "Zet iets bij de ander").status_code == 200
    agenda, task = gemini.tool_results()
    assert agenda == {"error": "Geen rechten om agenda te beheren voor deze gebruiker"}
    assert task == {"error": "Geen rechten om taken te beheren voor deze gebruiker"}
    assert agenda_titles(other["id"]) == set()


def test_imported_items_stay_read_only(client, make_user, configured, gemini):
    person, headers = make_user("Feed")
    db = SessionLocal()
    try:
        feed = PersonService(db).add_feed(person["id"], "https://example.test/a.ics", "A")
        item = AgendaItem(person_id=person["id"], title="Uit feed", source="ical", feed_id=feed.id, anchor_date=DAY)
        db.add(item)
        db.commit()
        item_id = item.id
    finally:
        db.close()
    gemini.call("update_agenda_item", id=item_id, title="Anders").call("delete_agenda_item", id=item_id).reply("Nee")
    send(client, headers, "Wijzig de training")
    update, delete = gemini.tool_results()
    assert update == {"error": "Agenda-items uit een feed kunnen niet worden bewerkt"}
    assert delete == {"error": "Agenda-items uit een feed kunnen niet worden verwijderd"}
    db = SessionLocal()
    try:
        assert db.get(AgendaItem, item_id).title == "Uit feed"
    finally:
        db.close()


# --- confirmation, conversation, limits (REQ-BE-086, REQ-BE-087, REQ-BE-088) -----------------------


def test_delete_needs_confirmation_in_a_later_message(client, make_user, configured, gemini):
    person, headers = make_user("Wissen")
    gemini.call("create_agenda_item", person_id=person["id"], title="Tandarts", date=DAY.isoformat()).reply("Ok")
    send(client, headers, "Tandarts erin")
    item_id = gemini.tool_results()[0]["created"]["id"]

    # Asking and 'confirming' within the same message does not delete.
    gemini.call("delete_agenda_item", id=item_id).call("delete_agenda_item", id=item_id, confirmed=True)
    gemini.reply("Weet je het zeker?")
    send(client, headers, "Haal de tandarts weg")
    first, second = gemini.tool_results()
    assert first["needs_confirmation"] and second["needs_confirmation"]
    assert agenda_titles(person["id"]) == {"Tandarts"}

    gemini.call("delete_agenda_item", id=item_id, confirmed=True).reply("Verwijderd")
    send(client, headers, "Ja")
    assert gemini.tool_results()[0]["deleted"]["title"] == "Tandarts"
    assert agenda_titles(person["id"]) == set()


def test_conversation_is_per_user_and_can_be_cleared(client, make_user, configured, gemini):
    _a, headers_a = make_user("Een")
    _b, headers_b = make_user("Twee")
    gemini.reply("Hoi Een")
    send(client, headers_a, "Hallo")
    messages = client.get("/api/ai/messages", headers=headers_a).json()
    assert [(m["role"], m["text"]) for m in messages] == [("user", "Hallo"), ("assistant", "Hoi Een")]
    assert messages[0]["created_at"].endswith("+00:00")
    assert client.get("/api/ai/messages", headers=headers_b).json() == []

    gemini.reply("Weer hoi")
    send(client, headers_a, "Nog een keer")
    sent = gemini.requests[-1]["contents"]
    assert [c["parts"][0]["text"] for c in sent] == ["Hallo", "Hoi Een", "Nog een keer"]

    assert client.delete("/api/ai/messages", headers=headers_a).json() == {"ok": True}
    assert client.get("/api/ai/messages", headers=headers_a).json() == []


def test_history_follows_the_context_setting(client, admin_headers, make_user, configured, gemini):
    person, headers = make_user("Lang")
    db = SessionLocal()
    try:
        for index in range(60):
            role = "user" if index % 2 == 0 else "assistant"
            db.add(ai_buddy.AiMessage(person_id=person["id"], role=role, text=f"bericht {index}"))
        db.commit()
    finally:
        db.close()
    send(client, headers, "Twintig")
    sent = gemini.requests[-1]["contents"]
    assert len(sent) == 20 and sent[-1]["parts"][0]["text"] == "Twintig"  # the default

    client.put("/api/admin/ai/config", headers=admin_headers, json={"context_messages": 5})
    send(client, headers, "Vijf")
    sent = gemini.requests[-1]["contents"]
    assert len(sent) == 5 and sent[-1]["parts"][0]["text"] == "Vijf"
    for bad in (1, 101):
        response = client.put("/api/admin/ai/config", headers=admin_headers, json={"context_messages": bad})
        assert response.status_code == 400


def test_at_most_ten_tool_calls_per_message(client, make_user, configured, gemini):
    _person, headers = make_user("Lus")
    for _ in range(12):
        gemini.call("search_tasks", start_date=DAY.isoformat(), end_date=DAY.isoformat())
    gemini.turns.insert(10, {"role": "model", "parts": [{"text": "Genoeg gezocht"}]})
    response = send(client, headers, "Zoek maar raak")
    assert response.json()["reply"]["text"] == "Genoeg gezocht"
    assert [r["allow_tools"] for r in gemini.requests] == [True] * 10 + [False]
    assert len(gemini.tool_results()) == 10


def test_transient_failures_are_retried(client, make_user, configured, monkeypatch):
    """REQ-BE-083: connection errors, timeouts and 5xx get two more attempts; 4xx does not."""
    import requests as real_requests

    _person, headers = make_user("Herhaal")
    delays = []
    monkeypatch.setattr(ai_buddy, "_sleep", delays.append)

    class Response:
        def __init__(self, status, payload):
            self.status_code, self._payload, self.text = status, payload, str(payload)

        def json(self):
            return self._payload

    ok = Response(200, {"candidates": [{"content": {"parts": [{"text": "Gelukt"}]}}]})
    script = [real_requests.ConnectionError("weg"), Response(503, {"error": {"message": "overloaded"}}), ok]

    def post(*_args, **_kwargs):
        item = script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(ai_buddy.requests, "post", post)
    response = send(client, headers, "Probeer maar")
    assert response.status_code == 200 and response.json()["reply"]["text"] == "Gelukt"
    assert delays == [1, 2]

    delays.clear()
    script[:] = [Response(400, {"error": {"message": "bad"}}), ok]
    assert send(client, headers, "Fout verzoek").status_code == 502
    assert delays == [] and script == [ok]


def test_switch_turns_the_ai_buddy_off(client, admin_headers, make_user, configured, gemini):
    """REQ-BE-081, REQ-BE-083: off keeps the settings but makes the AI buddy unavailable."""
    _person, headers = make_user("Schakelaar")
    cfg = client.put("/api/admin/ai/config", headers=admin_headers, json={"enabled": False}).json()
    assert cfg["enabled"] is False and cfg["configured"] is False
    assert cfg["has_api_key"] and cfg["model"] == "gemini-test"  # settings kept
    assert client.get("/api/ai/status", headers=headers).json() == {"configured": False}
    assert send(client, headers, "Hoi").status_code == 503

    client.put("/api/admin/ai/config", headers=admin_headers, json={"enabled": True})
    assert client.get("/api/ai/status", headers=headers).json() == {"configured": True}
    assert send(client, headers, "Hoi").status_code == 200


def test_new_settings_start_switched_off(client, admin_headers):
    """REQ-BE-081: on a fresh installation a key and a model alone do not switch the AI buddy on."""
    from app.models import AiConfig

    db = SessionLocal()
    try:
        db.query(AiConfig).delete()
        db.commit()
    finally:
        db.close()
    cfg = client.put(
        "/api/admin/ai/config", headers=admin_headers, json={"api_key": "AIza-x-0000", "model": "gemini-x"}
    ).json()
    assert cfg["enabled"] is False and cfg["configured"] is False and cfg["context_messages"] == 20
    client.put("/api/admin/ai/config", headers=admin_headers, json={"clear_api_key": True, "model": ""})


def test_thinking_level_is_validated_and_saved(client, admin_headers, configured):
    """REQ-BE-098: a thinking level is one of the known values, or empty for the model's default."""
    cfg = client.put("/api/admin/ai/config", headers=admin_headers, json={"thinking_level": "high"}).json()
    assert cfg["thinking_level"] == "high"
    assert cfg["thinking_levels"] == ["low", "medium", "high", "xhigh"]
    assert client.get("/api/admin/ai/config", headers=admin_headers).json()["thinking_level"] == "high"

    response = client.put("/api/admin/ai/config", headers=admin_headers, json={"thinking_level": "ultra"})
    assert response.status_code == 400

    cfg = client.put("/api/admin/ai/config", headers=admin_headers, json={"thinking_level": ""}).json()
    assert cfg["thinking_level"] == ""


def test_thinking_level_only_sent_to_gemini_3_and_4_models(client, admin_headers, make_user, configured, monkeypatch):
    """REQ-BE-098: thinkingLevel errors on older models, so it is only sent for Gemini 3/4 models."""
    _person, headers = make_user("Denker")
    requests_seen = []

    class Response:
        status_code = 200
        text = '{"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}'

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

    def post(*_args, **kwargs):
        requests_seen.append(kwargs["json"])
        return Response()

    monkeypatch.setattr(ai_buddy.requests, "post", post)

    client.put("/api/admin/ai/config", headers=admin_headers, json={"model": "gemini-test", "thinking_level": "high"})
    assert send(client, headers, "Hoi").status_code == 200
    assert "generationConfig" not in requests_seen[-1]

    client.put("/api/admin/ai/config", headers=admin_headers, json={"model": "gemini-3-flash-preview"})
    assert send(client, headers, "Hoi nog een keer").status_code == 200
    assert requests_seen[-1]["generationConfig"] == {"thinkingConfig": {"thinkingLevel": "HIGH"}}
