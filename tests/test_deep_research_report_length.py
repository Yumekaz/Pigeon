import asyncio

import pytest

from src.deep_research import DeepResearcher, _requested_report_word_limit


@pytest.mark.parametrize('question,limit', [
    ('Produce a report under 100 words with citations.', 100),
    ('At most 250 words. Up to 100 words in the conclusion.', 100),
    ('Use no more than 80 words.', 80),
    ('Write a detailed report about 100 products.', None),
    ('Analyze a source that mentions 100 words.', None),
])
def test_explicit_report_upper_bound(question, limit):
    assert _requested_report_word_limit(question) == limit


def researcher():
    r = DeepResearcher.__new__(DeepResearcher)
    r.category = 'factcheck'
    r.max_report_tokens = 512
    r._source_state_summary = lambda: 'One official source: https://docs.python.org/'
    r._source_coverage_json = lambda: '{}'
    r._navigation_trace_summary = lambda **kwargs: ''
    r._emit = lambda **kwargs: None
    return r


def test_short_report_preserves_citation_and_does_not_pay_for_expansion():
    r = researcher()
    calls = []
    async def llm(messages, **kwargs):
        calls.append(messages)
        return 'Supported by [official documentation](https://docs.python.org/). One primary source.'
    r._llm = llm
    result = asyncio.run(r._final_report('Verify the defaults in under 100 words.', 'Observed defaults.'))
    assert len(calls) == 1
    assert 'at most 100 words' in calls[0][0]['content']
    assert '1500' not in calls[0][0]['content']
    assert 'https://docs.python.org/' in result


def test_default_long_report_keeps_existing_expansion_behavior():
    r = researcher()
    calls = []
    async def llm(messages, **kwargs):
        calls.append(messages)
        return 'short report' if len(calls) == 1 else 'expanded report with evidence'
    r._llm = llm
    assert asyncio.run(r._final_report('Write a detailed report.', 'Evidence.')) == 'expanded report with evidence'
    assert len(calls) == 2
