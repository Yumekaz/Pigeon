import pytest

from src.agent_evidence import infer_completion_requirements
from src.turn_contract import requested_capabilities, selected_tools_for_request, required_read_operation_for_request


REQUEST = ('Use manage_documents to list saved editor documents matching hello-pigeon-complete.html, '
           'then read the matching document. Report its exact title and its HTML h1 text in one sentence. '
           'This is the editor library, not indexed personal documents.')


def test_explicit_saved_document_read_does_not_require_workspace_write():
    assert selected_tools_for_request(REQUEST) == {'manage_documents'}
    assert requested_capabilities(REQUEST) == {'documents'}
    assert required_read_operation_for_request(REQUEST) is None
    requirements = infer_completion_requirements(REQUEST)
    assert not requirements.required_artifacts
    assert not requirements.document_output_mode


@pytest.mark.parametrize('text', [
    'Read the saved document hello.html in the document editor.',
    'List generated documents matching report.pdf.',
])
def test_saved_source_is_not_an_output_artifact(text):
    requirements = infer_completion_requirements(text)
    assert not requirements.required_artifacts
    assert not requirements.document_output_mode


def test_read_then_create_still_requires_the_new_output():
    requirements = infer_completion_requirements('Read saved document input.html, then create output.html in my workspace.')
    assert requirements.required_artifacts == ('output.html',)
    assert selected_tools_for_request('Use manage_documents to read a draft, then write output.html in my workspace.') != {'manage_documents'}


@pytest.mark.parametrize('text', [
    'Use manage_documents to read a draft, then search the web for sources.',
    'Use manage_documents to read a draft, then list my emails.',
])
def test_other_store_reads_do_not_disappear_from_compound_request(text):
    assert selected_tools_for_request(text) != {'manage_documents'}
