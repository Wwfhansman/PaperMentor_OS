from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unicodedata import east_asian_width

from papermentor_os.schemas.report import FinalReport, PriorityAction, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity


PAGE_WIDTH = 595.0
PAGE_HEIGHT = 842.0
LEFT_MARGIN = 48.0
RIGHT_MARGIN = 48.0
TOP_MARGIN = 56.0
BOTTOM_MARGIN = 56.0

TITLE_FONT_SIZE = 20
SECTION_FONT_SIZE = 15
BODY_FONT_SIZE = 11
META_FONT_SIZE = 9
LINE_GAP = 6.0

DIMENSION_LABELS = {
    Dimension.TOPIC_SCOPE: "选题价值与问题清晰度",
    Dimension.LOGIC_CHAIN: "逻辑与论证链路",
    Dimension.LITERATURE_SUPPORT: "文献支撑",
    Dimension.NOVELTY_DEPTH: "创新性与研究深度",
    Dimension.WRITING_FORMAT: "写作与格式规范",
}

SEVERITY_LABELS = {
    Severity.HIGH: "高",
    Severity.MEDIUM: "中",
    Severity.LOW: "低",
}


@dataclass(frozen=True)
class _StyledLine:
    text: str
    font_size: int


class PdfReportExporter:
    """Export FinalReport to a minimal multi-page PDF without extra dependencies."""

    def export(
        self,
        report: FinalReport,
        *,
        paper_title: str,
        output_path: str | Path,
    ) -> Path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.render(report, paper_title=paper_title))
        return destination

    def render(self, report: FinalReport, *, paper_title: str) -> bytes:
        pages = self._paginate(self._build_lines(report, paper_title=paper_title))
        return self._build_pdf_document(pages)

    def _build_lines(self, report: FinalReport, *, paper_title: str) -> list[_StyledLine]:
        lines: list[_StyledLine] = [
            _StyledLine(f"{paper_title} 评审报告", TITLE_FONT_SIZE),
            _StyledLine(f"生成时间：{report.generated_at.isoformat()}", META_FONT_SIZE),
            _StyledLine("", BODY_FONT_SIZE),
            _StyledLine("总体总结", SECTION_FONT_SIZE),
            _StyledLine(report.overall_summary, BODY_FONT_SIZE),
            _StyledLine("", BODY_FONT_SIZE),
            _StyledLine("高优先级问题", SECTION_FONT_SIZE),
        ]

        if report.priority_actions:
            for index, action in enumerate(report.priority_actions, start=1):
                lines.extend(self._build_priority_action_lines(index, action))
        else:
            lines.append(_StyledLine("当前未发现高优先级问题。", BODY_FONT_SIZE))

        lines.extend(
            [
                _StyledLine("", BODY_FONT_SIZE),
                _StyledLine("维度评审结果", SECTION_FONT_SIZE),
            ]
        )

        for report_item in report.dimension_reports:
            lines.append(
                _StyledLine(
                    f"{DIMENSION_LABELS[report_item.dimension]} | 评分：{report_item.score:.1f}/10 | Debate：{'是' if report_item.debate_used else '否'}",
                    BODY_FONT_SIZE,
                )
            )
            lines.append(_StyledLine(f"摘要：{report_item.summary}", BODY_FONT_SIZE))
            if report_item.findings:
                for finding in report_item.findings:
                    lines.extend(self._build_finding_lines(finding))
            else:
                lines.append(_StyledLine("未识别到需重点展开的问题。", BODY_FONT_SIZE))
            lines.append(_StyledLine("", BODY_FONT_SIZE))

        lines.extend(
            [
                _StyledLine("学生修改建议", SECTION_FONT_SIZE),
                *[
                    _StyledLine(f"{index}. {step}", BODY_FONT_SIZE)
                    for index, step in enumerate(report.student_guidance.next_steps, start=1)
                ],
                _StyledLine("", BODY_FONT_SIZE),
                _StyledLine("导师快速查看", SECTION_FONT_SIZE),
                _StyledLine(report.advisor_view.quick_summary, BODY_FONT_SIZE),
            ]
        )

        if report.advisor_view.watch_points:
            lines.extend(
                _StyledLine(f"- {watch_point}", BODY_FONT_SIZE)
                for watch_point in report.advisor_view.watch_points
            )

        lines.extend(
            [
                _StyledLine("", BODY_FONT_SIZE),
                _StyledLine("安全提示", SECTION_FONT_SIZE),
                _StyledLine(report.safety_notice, BODY_FONT_SIZE),
            ]
        )
        return lines

    def _build_priority_action_lines(
        self,
        index: int,
        action: PriorityAction,
    ) -> list[_StyledLine]:
        return [
            _StyledLine(
                f"{index}. [{SEVERITY_LABELS[action.severity]}] {DIMENSION_LABELS[action.dimension]}：{action.title}",
                BODY_FONT_SIZE,
            ),
            _StyledLine(f"原因：{action.why_it_matters}", BODY_FONT_SIZE),
            _StyledLine(f"建议：{action.next_action}", BODY_FONT_SIZE),
            _StyledLine(f"证据锚点：{action.anchor_id}", BODY_FONT_SIZE),
        ]

    def _build_finding_lines(self, finding: ReviewFinding) -> list[_StyledLine]:
        return [
            _StyledLine(
                f"- [{SEVERITY_LABELS[finding.severity]}] {finding.issue_title}（置信度 {finding.confidence:.2f}）",
                BODY_FONT_SIZE,
            ),
            _StyledLine(f"  诊断：{finding.diagnosis}", BODY_FONT_SIZE),
            _StyledLine(f"  重要性：{finding.why_it_matters}", BODY_FONT_SIZE),
            _StyledLine(f"  修改建议：{finding.next_action}", BODY_FONT_SIZE),
            _StyledLine(
                f"  证据：{finding.evidence_anchor.location_label} / {finding.evidence_anchor.quote}",
                BODY_FONT_SIZE,
            ),
        ]

    def _paginate(self, lines: list[_StyledLine]) -> list[list[tuple[_StyledLine, float]]]:
        expanded_lines: list[_StyledLine] = []
        for line in lines:
            wrapped_lines = self._wrap_text(line.text, font_size=line.font_size)
            expanded_lines.extend(_StyledLine(wrapped_line, line.font_size) for wrapped_line in wrapped_lines)

        pages: list[list[tuple[_StyledLine, float]]] = [[]]
        current_y = PAGE_HEIGHT - TOP_MARGIN
        for line in expanded_lines:
            line_height = line.font_size + LINE_GAP
            if current_y - line_height < BOTTOM_MARGIN:
                pages.append([])
                current_y = PAGE_HEIGHT - TOP_MARGIN
            pages[-1].append((line, current_y))
            current_y -= line_height
        return pages

    def _wrap_text(self, text: str, *, font_size: int) -> list[str]:
        if not text:
            return [""]

        max_units = max(12.0, (PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN) / font_size)
        wrapped: list[str] = []
        current: list[str] = []
        current_units = 0.0

        for character in text:
            if character == "\n":
                wrapped.append("".join(current).rstrip())
                current = []
                current_units = 0.0
                continue

            char_units = self._char_units(character)
            if current and current_units + char_units > max_units:
                wrapped.append("".join(current).rstrip())
                current = [] if character == " " else [character]
                current_units = 0.0 if character == " " else char_units
                continue

            if not current and character == " ":
                continue

            current.append(character)
            current_units += char_units

        if current or not wrapped:
            wrapped.append("".join(current).rstrip())
        return wrapped

    def _char_units(self, character: str) -> float:
        if east_asian_width(character) in {"F", "W", "A"}:
            return 1.0
        return 0.55

    def _build_pdf_document(self, pages: list[list[tuple[_StyledLine, float]]]) -> bytes:
        content_streams = [self._render_page(page) for page in pages]

        objects: list[bytes] = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            self._build_pages_object(content_streams),
            (
                b"<< /Type /FontDescriptor /FontName /STSong-Light /Flags 4 "
                b"/FontBBox [-25 -254 1000 880] /ItalicAngle 0 /Ascent 752 "
                b"/Descent -271 /CapHeight 737 /StemV 80 >>"
            ),
            (
                b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light "
                b"/CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 4 >> "
                b"/FontDescriptor 3 0 R /DW 1000 >>"
            ),
            (
                b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light "
                b"/Encoding /UniGB-UCS2-H /DescendantFonts [4 0 R] >>"
            ),
        ]

        page_object_refs: list[int] = []
        next_object_id = 6
        for stream in content_streams:
            content_object_id = next_object_id
            page_object_id = next_object_id + 1
            next_object_id += 2

            page_object_refs.append(page_object_id)
            objects.append(self._build_stream_object(stream))
            objects.append(
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH:.0f} {PAGE_HEIGHT:.0f}] "
                    f"/Resources << /Font << /F1 5 0 R >> >> /Contents {content_object_id} 0 R >>"
                ).encode("ascii")
            )

        objects[1] = (
            f"<< /Type /Pages /Kids [{' '.join(f'{ref} 0 R' for ref in page_object_refs)}] "
            f"/Count {len(page_object_refs)} >>"
        ).encode("ascii")

        return self._serialize_pdf(objects)

    def _build_pages_object(self, content_streams: list[bytes]) -> bytes:
        page_count = len(content_streams)
        placeholder_refs = " ".join("0 0 R" for _ in range(page_count))
        return f"<< /Type /Pages /Kids [{placeholder_refs}] /Count {page_count} >>".encode("ascii")

    def _render_page(self, page: list[tuple[_StyledLine, float]]) -> bytes:
        operations: list[str] = []
        for line, y_position in page:
            if not line.text:
                continue
            operations.extend(
                [
                    "BT",
                    f"/F1 {line.font_size} Tf",
                    f"1 0 0 1 {LEFT_MARGIN:.2f} {y_position:.2f} Tm",
                    f"<{self._encode_pdf_text(line.text)}> Tj",
                    "ET",
                ]
            )
        return "\n".join(operations).encode("ascii")

    def _encode_pdf_text(self, text: str) -> str:
        return text.encode("utf-16-be").hex().upper()

    def _build_stream_object(self, stream: bytes) -> bytes:
        header = f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
        return header + stream + b"\nendstream"

    def _serialize_pdf(self, objects: list[bytes]) -> bytes:
        buffer = bytearray(b"%PDF-1.4\n%\xC7\xEC\x8F\xA2\n")
        offsets = [0]
        for object_id, payload in enumerate(objects, start=1):
            offsets.append(len(buffer))
            buffer.extend(f"{object_id} 0 obj\n".encode("ascii"))
            buffer.extend(payload)
            buffer.extend(b"\nendobj\n")

        xref_offset = len(buffer)
        buffer.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        buffer.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            buffer.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

        buffer.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF"
            ).encode("ascii")
        )
        return bytes(buffer)
