import pytest

from src.agent_tools.document_tools import _parse_create_document, document_tool_event_metadata


HTML = '<!doctype html>\n<html><head><title>PIGEON Demo</title></head>\n<body><h1>Hello PIGEON</h1></body></html>'


@pytest.mark.parametrize('payload', [
    'hello-pigeon.html\nhtml\n' + HTML,
    '<title>hello-pigeon.html</title>\n<language>html</language>\n<content>' + HTML + '</content>',
    'hello-pigeon.html\n<language>html</language>\n<content>' + HTML + '</content>',
])
def test_html_body_is_preserved_without_metadata(payload):
    assert _parse_create_document(payload) == ('hello-pigeon.html', 'html', HTML)


def test_markup_in_plain_document_body_is_not_stripped():
    body = 'Example: <title>keep me</title> and <content>keep this</content>'
    assert _parse_create_document('Reference\nmarkdown\n' + body) == ('Reference', 'markdown', body)


def test_content_root_in_xml_source_is_not_a_tool_envelope():
    assert _parse_create_document('sample.xml\nxml\n<content>keep this</content>') == (
        'sample.xml', 'xml', '<content>keep this</content>')


def test_content_line_is_not_mistaken_for_a_language():
    assert _parse_create_document('Note\nThis is prose') == ('Note', None, 'This is prose')


def test_approved_document_event_includes_exact_saved_source():
    metadata = document_tool_event_metadata({'doc_id': 'owned-doc', 'title': 'hello-pigeon.html',
        'language': 'html', 'content': HTML, 'version': 1, 'action': 'create'})
    assert metadata['document_content'] == HTML
    assert metadata['document_title'] == 'hello-pigeon.html'
    assert metadata['document_language'] == 'html'
    assert document_tool_event_metadata({'doc_id': 'doc-only'}) == {}


async def test_real_document_commit_produces_completion_receipt(tmp_path, monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import core.database as core_db
    import src.database as source_db
    import src.agent_tools.document_tools as documents
    from src.agent_evidence import EvidenceLedger, infer_completion_requirements
    from src.agent_runtime.journal import ActionJournal, ActionReceipt

    engine = create_engine(f'sqlite:///{tmp_path / "documents.db"}')
    core_db.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(source_db, 'SessionLocal', factory)
    monkeypatch.setattr(documents, '_active_document_id', None)
    monkeypatch.setattr('src.event_bus.fire_event', lambda *args: None)
    try:
        with factory() as db:
            db.add(core_db.Session(id='qa-chat', owner='qa', name='QA', endpoint_url='http://fixture', model='fixture'))
            db.commit()
        payload = 'hello-pigeon.html\nhtml\n' + HTML
        result = await documents.CreateDocumentTool().execute(payload, {'session_id': 'qa-chat', 'owner': 'qa'})
        assert result['exit_code'] == 0
        metadata = document_tool_event_metadata(result)
        assert metadata['document_artifacts'] == ['hello-pigeon.html']
        with factory() as db:
            saved = db.query(core_db.Document).filter_by(id=result['doc_id'], owner='qa').one()
            assert saved.title == 'hello-pigeon.html'
            assert saved.current_content == HTML
        action = ActionReceipt('action', 'call', 'create_document', payload, tool='create_document',
                               arguments=payload, execution_id='execution')
        action.finish(result)
        requirements = infer_completion_requirements(
            'Create a new HTML document named hello-pigeon.html in the document editor.')
        journal = ActionJournal(actions=[action])
        assert EvidenceLedger.from_tool_events(journal.evidence_events(), requirements).evaluate().can_complete
    finally:
        engine.dispose()
