"""Small dependency-free BM25 retriever over markdown guideline files."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9_]+")
STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "for", "on", "be", "with", "as", "that"}


@dataclass
class Chunk:
    source: str
    heading: str
    text: str

    @property
    def label(self) -> str:
        return f"{self.source} > {self.heading}"


@dataclass
class Hit:
    chunk: Chunk
    score: float


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


def chunk_markdown(text: str, source: str, max_chars: int = 1200) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading, buf = source, []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if not body:
            return
        for i in range(0, len(body), max_chars):
            chunks.append(Chunk(source, heading, body[i : i + max_chars]))

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            buf = []
            heading = line.lstrip("#").strip() or source
        else:
            buf.append(line)
    flush()
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self._tf = [Counter(tokenize(c.heading + " " + c.text)) for c in chunks]
        self._len = [sum(tf.values()) for tf in self._tf]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0
        df: Counter[str] = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        n = len(chunks)
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    @classmethod
    def from_dir(cls, directory: str | Path | None = None) -> "Retriever":
        folder = Path(directory) if directory else Path(__file__).resolve().parent.parent / "guidelines"
        chunks: list[Chunk] = []
        if folder.is_dir():
            for path in sorted(folder.glob("*.md")):
                chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.name))
        return cls(chunks)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        terms = tokenize(query)
        hits: list[Hit] = []
        for chunk, tf, length in zip(self.chunks, self._tf, self._len, strict=True):
            score = 0.0
            for term in terms:
                f = tf.get(term, 0)
                if not f:
                    continue
                denom = f + 1.5 * (1 - 0.75 + 0.75 * length / (self._avg or 1))
                score += self._idf.get(term, 0.0) * f * 2.5 / denom
            if score > 0:
                hits.append(Hit(chunk, score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]
