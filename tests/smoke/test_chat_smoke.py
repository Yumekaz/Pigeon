"""Chat: a turn against the stub provider comes back rendered and saved.

The buffered and the streamed path are both checked because the UI uses
the streamed one and the agent's own loop uses the buffered one, and a
decomposition can break either alone.
"""
from __future__ import annotations

import json

from tests.smoke.stub_provider import MODEL_PRIMARY, reply_for

CHAT_PATH = "/api/chat"
CHAT_STREAM_PATH = "/api/chat_stream"
HISTORY_PATH = "/api/history"

PROMPT = "Smoke check: reply with anything."


def test_buffered_turn_returns_the_provider_reply(client, chat_session, stub_provider):
    response = client.post(CHAT_PATH, json={"message": PROMPT, "session": chat_session})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("response") == reply_for(MODEL_PRIMARY), body
    assert body.get("model") == MODEL_PRIMARY, body
    # The app prefaces the turn with its own date/time context block, so
    # the prompt is contained in what the provider saw rather than equal
    # to it.
    assert any(PROMPT in seen for seen in stub_provider.recorder.prompts()), (
        "the prompt never reached the provider, so the reply came from "
        "somewhere other than the model path"
    )


def test_streamed_turn_emits_the_reply_and_saves_the_message(client, chat_session):
    deltas, saved = [], []
    with client.stream("POST", CHAT_STREAM_PATH,
                       json={"message": PROMPT, "session": chat_session}) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[len("data: "):].strip()
            if payload == "[DONE]":
                break
            try:
                event = json.loads(payload)
            except ValueError:
                continue
            if "delta" in event:
                deltas.append(str(event["delta"]))
            if event.get("type") == "message_saved":
                saved.append(event.get("id"))

    assert "".join(deltas) == reply_for(MODEL_PRIMARY), deltas
    assert saved and saved[0], "the stream never reported the assistant turn as saved"


def test_the_turn_is_in_the_session_history(client, chat_session):
    client.post(CHAT_PATH, json={"message": PROMPT, "session": chat_session})
    response = client.get(f"{HISTORY_PATH}/{chat_session}")
    assert response.status_code == 200, response.text
    messages = response.json().get("history") or []
    rendered = [str(m.get("content") or "") for m in messages]
    assert any(PROMPT in text for text in rendered), rendered
    assert any(reply_for(MODEL_PRIMARY) in text for text in rendered), rendered


def test_authenticated_native_document_read_runs_through_owned_tool_gate(client, stub_endpoint, stub_provider):
    from tests.smoke.stub_provider import MODEL_LUNA
    session = client.post("/api/session", data={"name": "PIGEON native tools", "endpoint_id": stub_endpoint, "model": MODEL_LUNA})
    assert session.status_code == 200, session.text
    session_id = session.json()["id"]
    document_id = None
    try:
        created = client.post("/api/document", json={"title": "PIGEON native tool fixture", "content": stub_provider.recorder.native_document_reply, "language": "text"})
        assert created.status_code == 200, created.text
        document_id = created.json()["id"]
        stub_provider.recorder.native_document_id = document_id
        before = len(stub_provider.recorder.calls)
        response = client.post(CHAT_STREAM_PATH, data={
            "message": f"Use manage_documents to read document {document_id}, then quote its first sentence. Do not edit anything.",
            "session": session_id, "mode": "agent",
            "active_doc_state": "closed",
        })
        assert response.status_code == 200, response.text
        parsed = []
        for line in response.text.splitlines():
            if line.startswith('data: ') and line[6:] != '[DONE]':
                try:
                    parsed.append(json.loads(line[6:]))
                except ValueError:
                    pass
        approval = next((event.get('data') for event in parsed if event.get('type') == 'ask_user'
                         and isinstance(event.get('data'), dict) and event['data'].get('kind') == 'tool_approval'), None)
        if approval:
            assert approval.get('action', {}).get('tool') == 'manage_documents'
            resumed = client.post(CHAT_STREAM_PATH, data={'session': session_id, 'message': 'Continue the read-only fixture task.',
                'mode': 'agent', 'tool_approval_id': approval['approval_id'], 'tool_approval_decision': 'approve_task', 'active_doc_state': 'closed'})
            assert resumed.status_code == 200, resumed.text
            from types import SimpleNamespace
            response = SimpleNamespace(text=response.text+resumed.text)
        assert stub_provider.recorder.native_document_reply in response.text, response.text
        assert "STUB-DOCUMENT-READ-FAILED" not in response.text, response.text
        calls = stub_provider.recorder.calls[before:]
        assert any("manage_documents" in str(call.get("tools")) for call in calls), calls
        # A successful read may finish deterministically without paying for
        # another provider round. Assert the executed result, not a mandatory
        # second model request.
        events = []
        for line in response.text.splitlines():
            if line.startswith('data: ') and line[6:] != '[DONE]':
                try:
                    events.append(json.loads(line[6:]))
                except ValueError:
                    pass
        assert any(event.get('type') == 'tool_output' and event.get('tool') == 'manage_documents'
                   and stub_provider.recorder.native_document_reply in str(event.get('output', ''))
                   and not event.get('blocked') for event in events), response.text
        assert client.get(f"/api/document/{document_id}").json()["current_content"] == stub_provider.recorder.native_document_reply
    finally:
        stub_provider.recorder.native_document_id = None
        if document_id:
            client.delete(f"/api/document/{document_id}")
        client.delete(f"/api/session/{session_id}")


def test_writing_menu_sends_bound_document_content_to_provider(client, stub_endpoint, stub_provider):
    from tests.smoke.stub_provider import MODEL_LUNA
    from tests.helpers.document_source import declaration
    import re
    prompt = dict(re.findall(r"\s+(\w+): '([^']+)'", declaration('_AI_WRITING_ACTIONS')))['concise']
    session = client.post('/api/session', data={'name': 'Writing context fixture', 'endpoint_id': stub_endpoint, 'model': MODEL_LUNA})
    session_id = session.json()['id']
    marker = 'PIGEON_BOUND_DOCUMENT_CONTENT_438729'
    doc = client.post('/api/document', json={'title': 'Bound context', 'content': marker, 'language': 'text', 'session_id': session_id})
    document_id = doc.json()['id']
    before = len(stub_provider.recorder.calls)
    try:
        response = client.post(CHAT_STREAM_PATH, data={'session': session_id, 'message': prompt,
            'mode': 'agent', 'active_doc_id': document_id, 'active_doc_state': 'visible'})
        assert response.status_code == 200
        calls = stub_provider.recorder.calls[before:]
        assert calls, response.text
        assert any(marker in str(message.get('content', '')) for call in calls for message in call.get('messages', [])), {
            'error': 'The active document was omitted from provider input',
            'message_roles': [[message.get('role') for message in call.get('messages', [])] for call in calls],
        }
        assert not any(marker in str(message.get('content', '')) for call in calls for message in call.get('messages', []) if message.get('role') == 'system'), 'Document source must not become system authority'
    finally:
        client.delete(f'/api/document/{document_id}')
        client.delete(f'/api/session/{session_id}')


def test_approved_suggestion_finishes_without_duplicate_model_calls(client, stub_endpoint, stub_provider):
    from tests.smoke.stub_provider import MODEL_LUNA
    session = client.post('/api/session', data={'name': 'Suggestion approval fixture', 'endpoint_id': stub_endpoint, 'model': MODEL_LUNA})
    session_id = session.json()['id']
    original = 'The PIGEON team is currently checking the editor.'
    replacement = 'The PIGEON team is checking the editor.'
    doc = client.post('/api/document', json={'title': 'Suggestion approval', 'content': original, 'language': 'text', 'session_id': session_id})
    document_id = doc.json()['id']
    stub_provider.recorder.native_suggestion_args = {'suggestions': [{'find': original, 'replace': replacement, 'reason': 'Remove unnecessary wording.'}]}
    def events(response):
        result = []
        for line in response.text.splitlines():
            if line.startswith('data: ') and line[6:] != '[DONE]':
                try:
                    result.append(json.loads(line[6:]))
                except ValueError:
                    pass
        return result
    try:
        response = client.post(CHAT_STREAM_PATH, data={'session': session_id, 'message': 'Make the open document more concise. Create inline suggestions only; do not apply changes.',
            'mode': 'agent', 'active_doc_id': document_id, 'active_doc_state': 'visible'})
        first = events(response)
        approval = next((e['data'] for e in first if e.get('type') == 'ask_user' and e.get('data', {}).get('kind') == 'tool_approval'), None)
        assert approval, response.text
        calls_before_resume = len(stub_provider.recorder.calls)
        resumed = client.post(CHAT_STREAM_PATH, data={'session': session_id, 'message': 'Continue the inline suggestion fixture task.',
            'mode': 'agent', 'tool_approval_id': approval['approval_id'], 'tool_approval_decision': 'approve_task',
            'active_doc_id': document_id, 'active_doc_state': 'visible'})
        finished = events(resumed)
        suggestions = [e for e in finished if e.get('type') == 'doc_suggestions']
        assert suggestions and suggestions[0]['suggestions'][0]['replace'] == replacement, resumed.text
        assert any(e.get('type') == 'final_response' and 'Added 1 inline suggestions' in str(e.get('content')) for e in finished), resumed.text
        assert len(stub_provider.recorder.calls) == calls_before_resume, 'Committed suggestions must not trigger a duplicate provider turn'
        assert client.get(f'/api/document/{document_id}').json()['current_content'] == original
    finally:
        stub_provider.recorder.native_suggestion_args = None
        client.delete(f'/api/document/{document_id}')
        client.delete(f'/api/session/{session_id}')
