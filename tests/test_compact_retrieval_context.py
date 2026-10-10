from types import SimpleNamespace

from src.clean_agent_preview import conversation
from src.prompt_security import untrusted_context_message


def test_current_indexed_document_reaches_compact_model_with_guard():
    reference = untrusted_context_message(
        'retrieved documents',
        '[pigeon-reference.txt]\nThe project codename is Amber Kite 73.',
    )
    request = {'role': 'user', 'content': 'What is the project codename?'}
    result = conversation(None, [reference, request])
    assert result == [reference, request]
    assert result[0] is not reference
    assert result[0]['role'] == 'user'
    assert result[0]['metadata']['trusted'] is False
    assert result[0]['metadata']['tool_gate_untrusted'] is True
    assert 'UNTRUSTED_SOURCE_DATA' in result[0]['content']


def test_retrieval_off_does_not_recover_old_document_from_trace():
    reference = untrusted_context_message('retrieved documents', 'old secret reference')
    history = SimpleNamespace(history=[
        {'role': 'user', 'content': 'Earlier request'},
        {'role': 'assistant', 'content': 'Earlier answer', 'metadata': {
            'rag_sources': [{'snippet': 'old secret reference'}],
        }},
    ])
    result = conversation(history, [{'role': 'user', 'content': 'New request'}])
    assert 'old secret reference' not in str(result)


def test_current_retrieval_survives_approval_history_rebuild():
    reference = untrusted_context_message('retrieved documents', '[reference.txt]\nBooth Maple 19.')
    history = SimpleNamespace(history=[
        {'role': 'user', 'content': 'Which booth?'},
        {'role': 'assistant', 'content': 'Allow this task to continue?'},
    ])
    result = conversation(history, [reference, {'role': 'user', 'content': 'Which booth?'}])
    assert result[0] == reference
    assert result[0]['metadata']['trusted'] is False
    assert result[-1]['content'] == 'Which booth?'
