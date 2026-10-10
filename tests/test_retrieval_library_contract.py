from types import SimpleNamespace

from src.chat_processor import ChatProcessor
from src.tool_schemas import FUNCTION_TOOL_SCHEMAS


def test_indexed_evidence_is_separate_from_editor_library_and_stays_untrusted():
    calls = []

    class Rag:
        def search(self, message, *, k, owner):
            calls.append(owner)
            return [{'document': 'QA project codename Amber Kite 73.',
                     'similarity': 0.8, 'metadata': {'filename': 'qa-reference.txt'}}]

    processor = ChatProcessor(memory_manager=None,
                              personal_docs_manager=SimpleNamespace(rag_manager=Rag()))
    preface, sources, _ = processor.build_context_preface(
        message='What is my project codename?', session=SimpleNamespace(),
        owner='qa-owner', use_rag=True, use_memory=False, use_skills=False,
    )
    assert calls == ['qa-owner']
    assert sources[0]['filename'] == 'qa-reference.txt'
    retrieved = next(m for m in preface if m.get('metadata', {}).get('source') == 'retrieved documents')
    assert retrieved['role'] == 'user'
    assert retrieved['metadata']['trusted'] is False
    assert retrieved['metadata']['tool_gate_untrusted'] is True
    system = '\n'.join(m['content'] for m in preface if m['role'] == 'system')
    assert 'manage_documents does not search this index' in system
    assert 'Amber Kite 73' not in system
    assert 'qa-reference.txt' not in system
    schema = next(s for s in FUNCTION_TOOL_SCHEMAS if s['function']['name'] == 'manage_documents')
    assert 'separate from indexed personal documents' in schema['function']['description']


def test_retrieval_disabled_never_queries_index_or_injects_its_guidance():
    class Rag:
        def search(self, *args, **kwargs):
            raise AssertionError('retrieval is disabled')

    processor = ChatProcessor(memory_manager=None,
                              personal_docs_manager=SimpleNamespace(rag_manager=Rag()))
    preface, sources, _ = processor.build_context_preface(
        message='Hello', session=SimpleNamespace(), use_rag=False,
        use_memory=False, use_skills=False,
    )
    assert not sources
    assert 'Indexed personal-document search has already supplied' not in str(preface)
