import pytest

from src.turn_contract import requested_capabilities, selected_tools_for_request, standalone_code_request
from src.clean_agent_preview import compact_schemas
from src.tool_schemas import FUNCTION_TOOL_SCHEMAS


@pytest.mark.parametrize('text', [
    'write snake in python code', 'Build a calculator app',
    'Create a game in JavaScript', 'Make an SVG of a circle', 'just an svg',
    'Write a Python script to sort a list', 'Generate an HTML webpage',
])
def test_standalone_code_targets_editor(text):
    assert selected_tools_for_request(text) == {'create_document'}
    assert requested_capabilities(text) == {'documents'}


@pytest.mark.parametrize('text', [
    'Write snake.py in my repository', 'Create /tmp/snake.py in Python',
    'Build a game in this workspace', 'Make an SVG using Python',
    'Explain this Python code', 'Write an email about my game',
    'Create a task to write a Python script daily', 'Write a note about code',
    'Write a short example of Python code', 'Do not write any code',
    'Fix the code in this document',
])
def test_other_work_does_not_become_new_code_document(text):
    assert not standalone_code_request(text)


@pytest.mark.parametrize('text', ['Create output.html', 'Write logo.svg'])
def test_bare_file_suffix_does_not_create_editor_artifact_kind(text):
    assert not standalone_code_request(text)


def test_compact_editor_schema_retains_artifact_guidance():
    schema = next(s for s in compact_schemas(FUNCTION_TOOL_SCHEMAS, model='Ajax')
                  if s['function']['name'] == 'create_document')
    assert 'complete working implementation' in schema['function']['description']
    assert 'svg' in schema['function']['parameters']['properties']['language']['enum']


def test_format_only_creation_requires_resolved_document_authority():
    from src.clean_agent_preview import preview_call_allowed
    args = {'title': 'Shape', 'language': 'svg', 'content': '<svg />'}
    assert preview_call_allowed('create_document', args, 'just an svg',
        contract_required_tools={'create_document'}, turn_authorized_families={'documents'})
    assert not preview_call_allowed('create_document', args, 'just an svg')


@pytest.mark.parametrize('text', [
    'Create and save a new HTML document in the document editor. Set its name/title to hello.html. Save it, not just code in chat.',
    'Generate an HTML/CSS webpage containing <h1>Hello</h1>',
])
def test_prose_slashes_and_html_tags_are_not_filesystem_targets(text):
    assert selected_tools_for_request(text) == {'create_document'}


@pytest.mark.parametrize('text', [
    r'Create C:\qa\demo.html in HTML',
    'Write src/demo.py in Python',
])
def test_actual_windows_and_relative_paths_remain_filesystem_work(text):
    assert not standalone_code_request(text)


def test_negated_chat_mention_does_not_create_a_session():
    # The public selector must retain editor routing rather than selecting a
    # session because the later explanation mentions chat.
    text = 'Create an HTML webpage. Do not merely paste code in chat.'
    assert selected_tools_for_request(text) == {'create_document'}


@pytest.mark.parametrize('text', [
    'Retry fetching the official Python print() documentation from the search result already found: https://docs.python.org/3/library/functions.html#print . Read only the print section, return its link and one sentence explaining print().',
    'Read https://example.org/docs/manual and summarize it.',
    'Fetch https://docs.example.org/notes/calendar and return one sentence.',
])
def test_remote_documentation_words_do_not_require_editor_document_capability(text):
    assert selected_tools_for_request(text) == {'web_fetch'}
    assert requested_capabilities(text) == {'search_browser'}
