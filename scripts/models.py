"""Data models shared across the ingestion pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Analysis(BaseModel):
    """Structured LLM output for one source."""

    summary: str = ""
    main_ideas: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)

    def merge(self, other: Analysis) -> Analysis:
        def union(a: list[str], b: list[str]) -> list[str]:
            return a + [x for x in b if x not in a]

        return Analysis(
            summary=" ".join(s for s in (self.summary, other.summary) if s),
            main_ideas=union(self.main_ideas, other.main_ideas),
            claims=union(self.claims, other.claims),
            concepts=union(self.concepts, other.concepts),
            questions=union(self.questions, other.questions),
        )


class FrameRef(BaseModel):
    path: str
    time: str


class SourceDoc(BaseModel):
    """A raw source after parsing, before any LLM work."""

    raw_path: str
    source_type: str
    title: str
    author: str = ""
    source_url: str = ""
    captured_at: str = ""
    content_hash: str
    privacy: str
    body: str
    page_count: int = 0
    low_confidence_pages: list[int] = Field(default_factory=list)
    # Audio/video extraction (empty for documents).
    media_kind: str = ""  # "audio" | "video"
    duration_seconds: float = 0.0
    language: str = ""
    extraction_model: str = ""
    processed_paths: list[str] = Field(default_factory=list)
    frames: list[FrameRef] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
