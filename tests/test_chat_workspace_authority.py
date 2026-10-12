from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_chat_request_does_not_send_hidden_workspace():
    source = (ROOT / "static/js/chat.js").read_text(encoding="utf-8")
    assert "fd.append('workspace_execution', workspaceExecutionAllowed ? 'true' : 'false')" in source
    assert "if (_ws && workspaceExecutionAllowed)" in source
    assert "workspaceAgentIntent && workspaceExecutionAllowed" in source


def test_new_chat_clears_workspace_and_indicator():
    source = (ROOT / "static/app.js").read_text(encoding="utf-8")
    handler = source.split("async function _handleNewChatAction", 1)[1].split("const hasOpenDocument", 1)[0]
    assert "workspaceModule.setWorkspace('')" in handler


def test_final_policy_blocks_workspace_tools_after_contract_restoration():
    source = (ROOT / "routes/chat_routes.py").read_text(encoding="utf-8")
    final_guard = source.index('disabled_tools.update(_SFT_DISABLED_WORKSPACE_TOOLS | {"bash"})')
    assert final_guard > source.rindex("disabled_tools.difference_update(_turn_contract.offered)")
    assert final_guard < source.index("research_blocked_by_policy = bool(", final_guard)
