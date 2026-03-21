from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.schemas.types import Discipline, PaperStage


class Paragraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paragraph_id: str
    anchor_id: str
    text: str = Field(min_length=1)


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    heading: str = Field(min_length=1)
    level: int = Field(ge=1, le=6)
    paragraphs: list[Paragraph] = Field(default_factory=list)


class PaperReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_id: str
    anchor_id: str
    raw_text: str = Field(min_length=1)


class PaperPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    title: str = Field(min_length=1)
    discipline: Discipline = Discipline.COMPUTER_SCIENCE
    stage: PaperStage = PaperStage.DRAFT
    abstract: str = ""
    sections: list[Section] = Field(default_factory=list)
    references: list[PaperReference] = Field(default_factory=list)
    advisor_requirements: str | None = None
    school_format_rules: str | None = None
    language: str = "zh"
    source_path: str | None = None

    def iter_body_paragraphs(self) -> Iterable[Paragraph]:
        for section in self.sections:
            yield from section.paragraphs

    @property
    def body_text(self) -> str:
        return "\n".join(paragraph.text for paragraph in self.iter_body_paragraphs())

