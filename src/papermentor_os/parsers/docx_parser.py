from __future__ import annotations

import re
from pathlib import Path

from docx import Document

from papermentor_os.schemas.paper import PaperPackage, PaperReference, Paragraph, Section
from papermentor_os.schemas.types import Discipline, PaperStage
from papermentor_os.shared.text import normalize_whitespace


HEADING_STYLE_PATTERN = re.compile(r"heading\s*(\d+)", re.IGNORECASE)
NUMBERED_HEADING_PATTERN = re.compile(r"^\d+(?:\.\d+)*\s+")
ABSTRACT_TITLES = {"摘要", "abstract"}
REFERENCE_TITLES = {"参考文献", "references", "bibliography"}


class DocxPaperParser:
    """Parse V1 docx thesis drafts into a stable PaperPackage."""

    def parse_file(
        self,
        file_path: str | Path,
        *,
        stage: PaperStage = PaperStage.DRAFT,
        discipline: Discipline = Discipline.COMPUTER_SCIENCE,
    ) -> PaperPackage:
        path = Path(file_path)
        if path.suffix.lower() != ".docx":
            raise ValueError("V1 only supports .docx input.")

        document = Document(str(path))
        paragraphs = [
            {
                "text": normalize_whitespace(paragraph.text),
                "style": normalize_whitespace(getattr(paragraph.style, "name", "")),
            }
            for paragraph in document.paragraphs
        ]
        paragraphs = [item for item in paragraphs if item["text"]]
        if not paragraphs:
            raise ValueError("The docx file does not contain readable paragraphs.")

        title = paragraphs[0]["text"]
        body_items = paragraphs[1:]

        abstract_lines: list[str] = []
        sections: list[Section] = []
        references: list[PaperReference] = []

        current_section: Section | None = None
        mode = "body"
        section_counter = 0
        paragraph_counter = 0
        reference_counter = 0

        for item in body_items:
            text = item["text"]
            heading_level = self._heading_level(text, item["style"])
            lowered = text.lower()

            if heading_level is not None:
                if lowered in ABSTRACT_TITLES:
                    mode = "abstract"
                    current_section = None
                    continue
                if lowered in REFERENCE_TITLES:
                    mode = "references"
                    current_section = None
                    continue

                mode = "body"
                section_counter += 1
                current_section = Section(
                    section_id=f"sec-{section_counter:03d}",
                    heading=text,
                    level=heading_level,
                    paragraphs=[],
                )
                sections.append(current_section)
                continue

            if mode == "abstract":
                abstract_lines.append(text)
                continue

            if mode == "references":
                reference_counter += 1
                references.append(
                    PaperReference(
                        reference_id=f"ref-{reference_counter:03d}",
                        anchor_id=f"ref-{reference_counter:03d}",
                        raw_text=text,
                    )
                )
                continue

            if current_section is None:
                section_counter += 1
                current_section = Section(
                    section_id=f"sec-{section_counter:03d}",
                    heading="未命名章节",
                    level=1,
                    paragraphs=[],
                )
                sections.append(current_section)

            paragraph_counter += 1
            current_section.paragraphs.append(
                Paragraph(
                    paragraph_id=f"p-{paragraph_counter:04d}",
                    anchor_id=f"{current_section.section_id}-p-{len(current_section.paragraphs) + 1:03d}",
                    text=text,
                )
            )

        return PaperPackage(
            paper_id=path.stem,
            title=title,
            discipline=discipline,
            stage=stage,
            abstract="\n".join(abstract_lines),
            sections=sections,
            references=references,
            source_path=str(path),
        )

    def _heading_level(self, text: str, style_name: str) -> int | None:
        if style_name:
            matched = HEADING_STYLE_PATTERN.search(style_name)
            if matched:
                return max(1, min(6, int(matched.group(1))))
            if style_name in {"标题 1", "标题 2", "标题 3"}:
                return int(style_name.split()[-1])

        if text in ABSTRACT_TITLES | REFERENCE_TITLES:
            return 1

        if NUMBERED_HEADING_PATTERN.match(text):
            return min(text.count(".") + 1, 6)

        if len(text) <= 30 and not text.endswith(("。", ".", "；", ";")):
            return 1

        return None

