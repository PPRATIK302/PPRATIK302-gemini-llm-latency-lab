from pathlib import Path

from latency_lab.retrieval import LocalTfidfRetriever, build_safe_prompt, load_documents


def test_retrieval_finds_token_rotation_doc() -> None:
    docs = load_documents(Path("data/sample_documents.json"))
    retriever = LocalTfidfRetriever(docs)
    passages = retriever.search("How do I rotate an API token?", top_k=3)
    assert any(passage.document.id == "DOC-004" for passage in passages)
    prompt = build_safe_prompt("How do I rotate an API token?", passages)
    assert "---BEGIN CONTEXT---" in prompt
    assert "---BEGIN USER QUESTION---" in prompt

