"""Section links must survive the bounded excerpts used by research/tools."""
import httpx
import pytest

from services.search import content


@pytest.fixture
def fetch(monkeypatch, tmp_path):
    monkeypatch.setattr(content, 'CONTENT_CACHE_DIR', tmp_path)

    def run(html, fragment=''):
        url = 'https://example.org/reference' + fragment
        response = httpx.Response(200, text=html,
                                 headers={'Content-Type': 'text/html'},
                                 request=httpx.Request('GET', url))
        monkeypatch.setattr(content, '_get_public_url', lambda *a, **k: response)
        return content.fetch_webpage_content(url)
    return run


def test_late_definition_precedes_index_and_retains_body_and_links(fetch):
    html = ('<main><p>INDEX ' + 'unrelated ' * 5000 + '</p>'
            '<dl><dt id="print">print(*objects, end="\\n")</dt>'
            '<dd><p>Ends with a newline. <a href="/details">Details</a></p></dd></dl>'
            '<dl><dt id="next">Next function</dt><dd>Other definition</dd></dl></main>')
    result = fetch(html, '#print')
    for key in ['content', 'linked_content']:
        excerpt = result[key][:1000]
        assert excerpt.startswith('print(')
        assert 'Ends with a newline' in excerpt
        assert result[key].index('Ends with a newline') < result[key].index('INDEX')
        assert 'Other definition' in result[key]  # full-page context retained
    assert '[Details](<https://example.org/details>)' in result['linked_content'][:1000]


def test_heading_stops_at_next_peer_but_keeps_subheading(fetch):
    html = ('<main><p>Intro</p><h2 id="target">Target</h2><p>Requested text</p>'
            '<h3>Detail</h3><p>Nested text</p><h2>Other</h2><p>Unrelated</p></main>')
    result = fetch(html, '#target')
    section = result['content'].split('[Full page follows]')[0]
    assert 'Requested text' in section and 'Nested text' in section
    assert 'Unrelated' not in section


def test_encoded_nested_heading_anchor(fetch):
    result = fetch('<main><h2><span id="a:b">Named heading</span></h2>'
                   '<p>Section body</p><h2>End</h2></main>', '#a%3Ab')
    assert result['content'].startswith('Named heading\nSection body')


@pytest.mark.parametrize('fragment', ['', '#missing', '#:~:text=does-not-exist'])
def test_absent_anchor_preserves_normal_extraction(fetch, fragment):
    result = fetch('<main><p>Normal article</p></main>', fragment)
    assert result['content'] == 'Normal article'
    assert '[Full page follows]' not in result['linked_content']


def test_fragment_is_part_of_cache_identity(fetch):
    html = '<main><section id="one">First</section><section id="two">Second</section></main>'
    assert fetch(html, '#one')['content'].startswith('First\n\n')
    assert fetch(html, '#two')['content'].startswith('Second\n\n')
