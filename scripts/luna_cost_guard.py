"""Loopback-only, durable cost guard for authorized PIGEON live tests.

No reset endpoint. A pre-existing reconciled ledger is required. Secrets and
message bodies are never persisted. Only text and local function tools pass.
"""
import json
import os
import sqlite3
import ssl
import uuid
from contextlib import closing
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

MODEL = "gpt-6-luna"
# Pico-USD per token: worst cache-write/input and output rates,
# including the possible 10% regional premium, at Standard service tier.
INPUT_RATE = 137_500
OUTPUT_RATE = 550_000
MAX_INPUT = 32_768
MAX_OUTPUT = 512
LEDGER = Path(os.environ.get("PIGEON_TEST_COST_LEDGER", ".preview-runtime/luna-cost-ledger.sqlite3"))
app = FastAPI()


class BudgetBlocked(Exception):
    pass


def connect(path):
    if not Path(path).is_file():
        raise BudgetBlocked("Reconciled spending ledger is missing; no allowance was reset.")
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.execute("PRAGMA synchronous=FULL")
    return db


def initialize(path, reconciliation):
    """Explicit, one-time import; refuses to overwrite any existing ledger."""
    from decimal import Decimal
    path = Path(path)
    with path.open("xb"):
        pass
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE budget (id INTEGER PRIMARY KEY CHECK(id=1), ceiling INTEGER NOT NULL,
          historical INTEGER NOT NULL, frozen INTEGER NOT NULL DEFAULT 0, evidence TEXT NOT NULL);
        CREATE TABLE requests (id TEXT PRIMARY KEY, reserved INTEGER NOT NULL, charged INTEGER,
          state TEXT NOT NULL, input_tokens INTEGER, output_tokens INTEGER,
          created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE preflights (id TEXT PRIMARY KEY, state TEXT NOT NULL,
          created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
        db.execute("INSERT INTO budget VALUES(1,?,?,0,?)", (
            int(Decimal(reconciliation["approved_additional_budget_usd"])*10**12),
            int(Decimal(reconciliation["historical_reserved_usd"])*10**12),
            json.dumps(reconciliation, sort_keys=True)))


def snapshot(path=None):
    path = LEDGER if path is None else path
    try:
        with closing(connect(path)) as db:
            row = db.execute("SELECT ceiling,historical,frozen FROM budget WHERE id=1").fetchone()
            if row is None:
                raise BudgetBlocked("Spending ledger is incomplete; the allowance was not reset.")
            ceiling, historical, frozen = row
            held = db.execute("SELECT COALESCE(SUM(COALESCE(charged,reserved)),0) FROM requests").fetchone()[0]
            return {"model": MODEL, "ceiling_pico_usd": ceiling, "historical_pico_usd": historical,
                    "requests_pico_usd": held, "remaining_pico_usd": ceiling-historical-held,
                    "frozen": bool(frozen)}
    except sqlite3.DatabaseError as exc:
        raise BudgetBlocked("Spending ledger cannot be read; the allowance was not reset.") from exc


def reserve(input_tokens, output_tokens, path=None):
    path = LEDGER if path is None else path
    if type(input_tokens) is not int or not 0 <= input_tokens <= MAX_INPUT:
        raise BudgetBlocked("Exact input count is unavailable or exceeds the test context cap.")
    if type(output_tokens) is not int or not 1 <= output_tokens <= MAX_OUTPUT:
        raise BudgetBlocked("Output cap is invalid.")
    amount = input_tokens*INPUT_RATE + output_tokens*OUTPUT_RATE
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        ceiling, historical, frozen = db.execute("SELECT ceiling,historical,frozen FROM budget WHERE id=1").fetchone()
        held = db.execute("SELECT COALESCE(SUM(COALESCE(charged,reserved)),0) FROM requests").fetchone()[0]
        if frozen or amount > ceiling-historical-held:
            raise BudgetBlocked("The remaining authorized test budget cannot cover this request's maximum cost.")
        request_id = uuid.uuid4().hex
        db.execute("INSERT INTO requests(id,reserved,state,input_tokens) VALUES(?,?,'reserved',?)", (request_id, amount, input_tokens))
        db.commit()
        return request_id
    finally:
        db.close()


def settle(request_id, usage, path=None):
    path = LEDGER if path is None else path
    # Missing usage, disconnects and ambiguous failures retain the full hold.
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        reserved, state = db.execute("SELECT reserved,state FROM requests WHERE id=?", (request_id,)).fetchone()
        if state == "settled":
            raise ValueError("Request was already settled")
        valid = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens"))
        if not valid:
            db.execute("UPDATE requests SET state='usage_unknown' WHERE id=?", (request_id,))
        else:
            charged = usage["input_tokens"]*INPUT_RATE + usage["output_tokens"]*OUTPUT_RATE
            db.execute("UPDATE requests SET charged=?,state='settled',input_tokens=?,output_tokens=? WHERE id=?", (charged, usage["input_tokens"], usage["output_tokens"], request_id))
            if charged > reserved:
                db.execute("UPDATE budget SET frozen=1 WHERE id=1")
        db.commit()
    finally:
        db.close()


def payload_for(body):
    if not isinstance(body, dict) or body.get("model") != MODEL:
        raise ValueError("Only gpt-6-luna is authorized for live tests.")
    if body.get("n", 1) != 1 or body.get("functions"):
        raise ValueError("Multiple completions and legacy function calls are blocked.")
    items = []
    for message in body.get("messages", []):
        role, content = message.get("role"), message.get("content")
        if isinstance(content, list) and all(p.get("type") == "text" for p in content):
            content = "\n".join(p.get("text", "") for p in content)
        if role == "tool":
            if not isinstance(content, str) or not message.get("tool_call_id"):
                raise ValueError("Invalid tool result")
            items.append({"type": "function_call_output", "call_id": message["tool_call_id"], "output": content})
            continue
        if role not in {"system", "developer", "user", "assistant"}:
            raise ValueError("Unsupported message role")
        if content:
            if not isinstance(content, str):
                raise ValueError("Only text is permitted; image/audio charges are blocked.")
            items.append({"role": role, "content": content})
        for call in message.get("tool_calls", []):
            f = call["function"]
            items.append({"type": "function_call", "call_id": call["id"], "name": f["name"], "arguments": f["arguments"]})
    if not items:
        raise ValueError("Expected text input")
    tools = []
    for tool in body.get("tools", []):
        if tool.get("type") != "function":
            raise ValueError("Hosted tools and their additional charges are blocked.")
        f = tool["function"]
        tools.append({"type": "function", "name": f["name"], "description": f.get("description", ""), "parameters": f.get("parameters", {"type": "object", "properties": {}}), "strict": False})
    requested = body.get("max_completion_tokens", body.get("max_tokens", MAX_OUTPUT))
    if type(requested) is not int or requested < 1:
        raise ValueError("Invalid output limit")
    payload = {"model": MODEL, "input": items, "reasoning": {"effort": "none"},
               "max_output_tokens": min(requested, MAX_OUTPUT), "store": False,
               "service_tier": "default"}
    if tools:
        payload["tools"] = tools
    choice = body.get("tool_choice")
    if choice is not None:
        if choice in ("auto", "none", "required"):
            payload["tool_choice"] = choice
        elif isinstance(choice, dict) and choice.get("type") == "function":
            name = choice.get("function", {}).get("name")
            if not any(tool["name"] == name for tool in tools):
                raise ValueError("Forced tool is not among the offered functions")
            payload["tool_choice"] = {"type": "function", "name": name}
        else:
            raise ValueError("Unsupported tool choice")
    if "parallel_tool_calls" in body:
        payload["parallel_tool_calls"] = bool(body["parallel_tool_calls"])
    return payload


def blocked(message, code="budget_blocked", status=402):
    return JSONResponse({"error": {"type": "pigeon_budget_block", "origin": "pigeon_budget_guard",
        "code": code, "message": "PIGEON local test budget: " + message + " No OpenAI generation request was sent."}}, status_code=status)


@app.get("/status")
async def status():
    try:
        return snapshot()
    except BudgetBlocked as exc:
        return blocked(str(exc), "ledger_missing")


@app.get("/v1/models")
async def models():
    return {"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "openai"}]}


@app.post("/v1/chat/completions")
async def chat(request: Request):
    raw = await request.body()
    if len(raw) > 131072:
        return blocked("Request exceeds the local size cap.", "request_size", 413)
    try:
        body = json.loads(raw)
        payload = payload_for(body)
        current = snapshot()
        if current["frozen"] or current["remaining_pico_usd"] <= 0:
            raise BudgetBlocked("The authorized allowance is exhausted or held for reconciliation.")
    except BudgetBlocked as exc:
        return blocked(str(exc))
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return blocked(str(exc), "request_policy", 400)
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return blocked("Enter your key locally in PIGEON.", "credentials_missing", 400)
    headers = {"Authorization": auth, "Content-Type": "application/json"}
    # Token-count endpoint performs no generation. Its exact model-specific
    # count includes tool schemas and framing; do not use character estimates.
    preflight_id = uuid.uuid4().hex
    with connect(LEDGER) as db:
        db.execute("INSERT INTO preflights(id,state) VALUES(?,'started')", (preflight_id,))
    client = httpx.AsyncClient(timeout=60, verify=ssl.create_default_context(), follow_redirects=False)
    request_id = None
    try:
        count_payload = {k: payload[k] for k in ("model", "input", "tools", "tool_choice") if k in payload}
        count = await client.post("https://api.openai.com/v1/responses/input_tokens", headers=headers, json=count_payload)
        with connect(LEDGER) as db:
            db.execute("UPDATE preflights SET state=? WHERE id=?", (f"http_{count.status_code}", preflight_id))
        if count.status_code != 200:
            await client.aclose()
            return JSONResponse({"error": {"type": "openai_preflight_error", "message": "OpenAI rejected the token-count preflight; no generation was sent."}}, status_code=count.status_code)
        request_id = reserve(count.json().get("input_tokens"), payload["max_output_tokens"])
        payload["stream"] = True
        upstream = await client.send(client.build_request("POST", "https://api.openai.com/v1/responses", headers=headers, json=payload), stream=True)
        if upstream.status_code != 200:
            raw_error = await upstream.aread()
            settle(request_id, None)
            await upstream.aclose()
            await client.aclose()
            return JSONResponse(json.loads(raw_error), status_code=upstream.status_code)
    except BudgetBlocked as exc:
        await client.aclose()
        return blocked(str(exc))
    except (httpx.HTTPError, ValueError) as exc:
        if request_id:
            settle(request_id, None)
        await client.aclose()
        return JSONResponse({"error": {"type": "openai_connection_error", "message": "OpenAI transport/preflight failed; any generation reservation is retained. No automatic retry."}}, status_code=502)

    async def relay():
        usage = None
        text = []
        calls = {}
        def chunk(delta, finish=None, metrics=None):
            item = {"id": request_id, "object": "chat.completion.chunk", "model": MODEL,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
            if metrics is not None:
                item["usage"] = metrics
            return "data: " + json.dumps(item) + "\n\n"
        try:
            async for line in upstream.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                kind = event.get("type")
                if kind == "response.output_text.delta":
                    text.append(event["delta"])
                    if body.get("stream"):
                        yield chunk({"content": event["delta"]})
                elif kind == "response.output_item.added" and event.get("item", {}).get("type") == "function_call":
                    item = event["item"]
                    index = len(calls)
                    calls[event["output_index"]] = {"index": index, "id": item["call_id"], "type": "function", "function": {"name": item["name"], "arguments": item.get("arguments", "")}}
                    if body.get("stream"):
                        yield chunk({"tool_calls": [calls[event["output_index"]]]})
                elif kind == "response.function_call_arguments.delta":
                    call = calls[event["output_index"]]
                    call["function"]["arguments"] += event["delta"]
                    if body.get("stream"):
                        yield chunk({"tool_calls": [{"index": call["index"], "function": {"arguments": event["delta"]}}]})
                elif kind in {"response.completed", "response.incomplete"}:
                    response = event["response"]
                    usage = response.get("usage")
                    if response.get("model") != MODEL or response.get("service_tier", "default") != "default":
                        with connect(LEDGER) as db:
                            db.execute("UPDATE budget SET frozen=1 WHERE id=1")
                    metrics = {"prompt_tokens": usage["input_tokens"], "completion_tokens": usage["output_tokens"], "total_tokens": usage["input_tokens"]+usage["output_tokens"]} if usage else None
                    finish = "length" if kind == "response.incomplete" else "tool_calls" if calls else "stop"
                    if body.get("stream"):
                        yield chunk({}, finish, metrics)
                        yield "data: [DONE]\n\n"
                    else:
                        tool_calls = [{k: v for k, v in c.items() if k != "index"} for c in calls.values()]
                        message = {"role": "assistant", "content": "".join(text)}
                        if tool_calls:
                            message["tool_calls"] = tool_calls
                        yield json.dumps({"id": request_id, "model": MODEL, "object": "chat.completion", "choices": [{"index": 0, "message": message, "finish_reason": finish}], "usage": metrics})
                elif kind in {"error", "response.failed"}:
                    error = {"error": {"message": "OpenAI generation failed; the cost reservation is retained pending usage reconciliation.", "type": "openai_generation_error"}}
                    yield "data: " + json.dumps(error) + "\n\n" if body.get("stream") else json.dumps(error)
        finally:
            settle(request_id, usage)
            await upstream.aclose()
            await client.aclose()
    return StreamingResponse(relay(), media_type="text/event-stream" if body.get("stream") else "application/json")
