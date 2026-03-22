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
CONTENTS_TITLES = {"目录", "contents", "tableofcontents"}
TITLE_STYLE_HINTS = {"title", "标题", "论文题目"}
COVER_PAGE_HINTS = {"大学", "学院", "专业", "指导教师", "学号", "姓名", "班级"}
TITLE_KEYWORDS = {"评审", "论文", "研究", "设计", "实现", "框架", "分析", "系统", "方法", "适配"}
TOC_ENTRY_PATTERN = re.compile(
    r"^(?:第[一二三四五六七八九十百]+章|[一二三四五六七八九十]+、|\d+(?:\.\d+)*\s+).*(?:\.{2,}|\u2026{2,}|\s)\d+$"
)


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

        title_index = self._select_title_index(paragraphs)
        title = paragraphs[title_index]["text"]
        body_items = paragraphs[title_index + 1:]

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
            normalized_heading = self._canonical_heading_label(text)

            if mode == "contents" and self._is_table_of_contents_entry(text):
                continue

            if heading_level is not None:
                if normalized_heading in ABSTRACT_TITLES:
                    mode = "abstract"
                    current_section = None
                    continue
                if normalized_heading in CONTENTS_TITLES:
                    mode = "contents"
                    current_section = None
                    continue
                if normalized_heading in REFERENCE_TITLES:
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
        normalized_heading = self._canonical_heading_label(text)
        if style_name:
            matched = HEADING_STYLE_PATTERN.search(style_name)
            if matched:
                return max(1, min(6, int(matched.group(1))))
            if style_name in {"标题 1", "标题 2", "标题 3"}:
                return int(style_name.split()[-1])

        if normalized_heading in ABSTRACT_TITLES | REFERENCE_TITLES:
            return 1

        if NUMBERED_HEADING_PATTERN.match(text):
            return min(text.count(".") + 1, 6)

        if len(text) <= 30 and not text.endswith(("。", ".", "；", ";")):
            return 1

        return None

    def _canonical_heading_label(self, text: str) -> str:
        return re.sub(r"\s+", "", text).lower()

    def _is_table_of_contents_entry(self, text: str) -> bool:
        normalized = normalize_whitespace(text)
        return bool(TOC_ENTRY_PATTERN.match(normalized))

    def _select_title_index(self, paragraphs: list[dict[str, str]]) -> int:
        abstract_index = next(
            (
                index
                for index, item in enumerate(paragraphs)
                if self._canonical_heading_label(item["text"]) in ABSTRACT_TITLES
            ),
            len(paragraphs),
        )
        candidate_range = paragraphs[:abstract_index] or paragraphs[:1]

        scored_candidates: list[tuple[int, int]] = []
        for index, item in enumerate(candidate_range):
            text = item["text"]
            style_name = item["style"]
            score = 0
            canonical_style = style_name.lower()
            if any(hint in canonical_style for hint in TITLE_STYLE_HINTS):
                score += 6
            if any(keyword in text for keyword in TITLE_KEYWORDS):
                score += 2
            if 8 <= len(text) <= 40:
                score += 2
            if len(text) > 45:
                score -= 2
            if any(hint in text for hint in COVER_PAGE_HINTS):
                score -= 4
            if self._canonical_heading_label(text) in ABSTRACT_TITLES | REFERENCE_TITLES:
                score -= 10
            scored_candidates.append((score, index))

        best_score, best_index = max(scored_candidates, key=lambda item: (item[0], -item[1]))
        if best_score <= 0:
            return 0
        return best_index
