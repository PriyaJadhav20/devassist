from devassist.rag.retriever import Retriever, chunk_markdown


def test_chunking_by_heading():
    chunks = chunk_markdown("# T\n\n## One\nalpha beta\n\n## Two\ngamma", "x.md")
    assert [c.heading for c in chunks] == ["One", "Two"]


def test_default_guidelines_answer_sql_question():
    hit = Retriever.from_dir().search("sql injection parameterized queries", k=1)[0]
    assert "security.md" in hit.chunk.label


def test_no_match_returns_empty():
    assert Retriever.from_dir().search("zzzzqqq", k=3) == []
