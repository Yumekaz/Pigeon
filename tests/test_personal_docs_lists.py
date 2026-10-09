from src import personal_docs


def test_string_list_filters_non_strings():
    assert personal_docs._string_list(["/tmp/a", None, 3, "/tmp/b"]) == ["/tmp/a", "/tmp/b"]
    assert personal_docs._string_list(None) == []


def test_repeated_upload_directory_refreshes_files_without_reembedding(tmp_path):
    from unittest.mock import Mock
    root = tmp_path / "personal"
    uploads = root / "uploads"
    uploads.mkdir(parents=True)
    rag = Mock()
    manager = personal_docs.PersonalDocsManager(str(root), rag_manager=rag)
    (uploads / "first.txt").write_text("First document", encoding="utf-8")
    manager.add_directory(str(uploads), index=False)
    (uploads / "second.txt").write_text("Second document", encoding="utf-8")
    manager.add_directory(str(uploads), index=False)
    assert any("second.txt" in item["name"] for item in manager.index)
    rag.index_personal_documents.assert_not_called()
