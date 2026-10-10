from dataclasses import replace

import pytest

from src.agent_evidence import EvidenceLedger, infer_completion_requirements, requirements_from_runtime_context
from src.agent_runtime.completion import completion_answer
from src.agent_runtime.journal import ActionJournal, ActionReceipt


REQUEST = 'Create a new HTML document named hello-pigeon.html in the document editor. Actually save it.'


def receipt(result, *, dispatched=True):
    action = ActionReceipt('action-1', 'call-1', 'create_document', 'hello-pigeon.html\nhtml\n<body>Hello</body>')
    action.tool = 'create_document'
    action.arguments = action.proposed_arguments
    action.execution_id = 'execution-1' if dispatched else None
    action.finish(result)
    return action


def ledger_for(action, requirements):
    journal = ActionJournal(actions=[action])
    return EvidenceLedger.from_tool_events(journal.evidence_events(), requirements)


def test_saved_editor_document_satisfies_named_document_even_with_workspace(tmp_path):
    requirements = replace(infer_completion_requirements(REQUEST), workspace_root=str(tmp_path))
    assert requirements.document_artifacts == ('hello-pigeon.html',)
    action = receipt({'exit_code': 0, 'doc_id': 'owned-doc', 'title': 'hello-pigeon.html', 'version': 1})
    ledger = ledger_for(action, requirements)
    decision = ledger.evaluate()
    assert decision.can_complete
    answer, reason = completion_answer('I created hello-pigeon.html.', ledger, decision)
    assert 'incomplete' not in answer
    assert 'Document saved: hello-pigeon.html.' in answer
    assert 'No passing executable test' not in answer
    assert not (tmp_path / 'hello-pigeon.html').exists()


@pytest.mark.parametrize('result,dispatched', [
    ({'exit_code': 0}, True),
    ({'exit_code': 1, 'error': 'commit failed', 'doc_id': 'doc', 'title': 'hello-pigeon.html', 'version': 1}, True),
    ({'exit_code': 0, 'doc_id': 'doc', 'title': 'hello-pigeon.html', 'version': 1}, False),
])
def test_arguments_or_failed_undispatched_results_cannot_attest_saved_document(result, dispatched):
    ledger = ledger_for(receipt(result, dispatched=dispatched), infer_completion_requirements(REQUEST))
    assert not ledger.evaluate().can_complete


def test_document_receipt_does_not_satisfy_filesystem_request(tmp_path):
    requirements = replace(infer_completion_requirements('Write hello-pigeon.html in my workspace.'),
                           workspace_root=str(tmp_path))
    assert not requirements.document_artifacts
    action = receipt({'exit_code': 0, 'doc_id': 'doc', 'title': 'hello-pigeon.html', 'version': 1})
    assert not ledger_for(action, requirements).evaluate().can_complete


def test_approval_wait_is_not_presented_as_a_failed_task():
    ledger = EvidenceLedger(infer_completion_requirements(REQUEST))
    answer, _ = completion_answer('I created hello-pigeon.html.', ledger,
                                 ledger.evaluate(awaiting_user=True))
    assert 'Waiting for your response' in answer
    assert 'incomplete' not in answer
    assert 'I created' not in answer


def test_unnamed_code_document_has_receipt_backed_completion():
    requirements = infer_completion_requirements('Generate an HTML webpage in the document editor.')
    assert requirements.document_output_mode
    action = receipt({'exit_code': 0, 'doc_id': 'doc', 'title': 'Demo.html', 'version': 1})
    ledger = ledger_for(action, requirements)
    answer, reason = completion_answer('I created Demo.html.', ledger, ledger.evaluate())
    assert not reason
    assert answer == 'I created Demo.html.'


def test_filesystem_write_does_not_attest_an_editor_document(tmp_path):
    requirements = replace(infer_completion_requirements(REQUEST), workspace_root=str(tmp_path))
    (tmp_path / 'hello-pigeon.html').write_text('<html />', encoding='utf-8')
    ledger = EvidenceLedger.from_tool_events([{'tool': 'write_file',
        'command': 'hello-pigeon.html\n<html />', 'exit_code': 0}], requirements)
    assert not ledger.evaluate().can_complete


def test_internal_contract_roundtrip_preserves_document_kind_only_for_server():
    requirements = infer_completion_requirements(REQUEST)
    context = {'completion_requirements': requirements.to_dict()}
    assert requirements_from_runtime_context(context, _server_declared=True) == requirements
    assert not requirements_from_runtime_context(context).document_output_mode
    action = receipt({'exit_code': 0, 'doc_id': 'doc', 'title': 'hello-pigeon.html', 'version': 1})
    declared = requirements_from_runtime_context(context, _server_declared=True)
    assert ledger_for(action, declared).evaluate().can_complete
