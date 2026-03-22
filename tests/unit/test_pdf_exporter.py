from datetime import datetime, timezone
from pathlib import Path

from papermentor_os.reporting.pdf_exporter import PdfReportExporter
from papermentor_os.schemas.report import (
    AdvisorView,
    DimensionReport,
    EvidenceAnchor,
    FinalReport,
    PriorityAction,
    ReviewFinding,
    StudentGuidance,
)
from papermentor_os.schemas.types import Dimension, Severity


def test_pdf_report_exporter_writes_pdf_document(tmp_path: Path) -> None:
    exporter = PdfReportExporter()
    report = FinalReport(
        overall_summary="系统已生成结构化评审报告，当前最优先处理研究问题与实验验证闭环。",
        dimension_reports=[
            DimensionReport(
                dimension=Dimension.LOGIC_CHAIN,
                score=6.0,
                summary="逻辑链路存在验证不足的问题。",
                findings=[
                    ReviewFinding(
                        dimension=Dimension.LOGIC_CHAIN,
                        issue_title="论证链缺少明确的验证环节",
                        severity=Severity.HIGH,
                        confidence=0.8,
                        evidence_anchor=EvidenceAnchor(
                            anchor_id="sec-004",
                            location_label="实验评估",
                            quote="未识别到实验设计与评价指标。",
                        ),
                        diagnosis="当前正文对方法效果的判断主要停留在描述层。",
                        why_it_matters="没有验证环节会削弱研究结论的说服力。",
                        next_action="补充实验设计、评价指标和关键结果。",
                        source_agent="LogicChainAgent",
                        source_skill_version="logic-chain-rubric@0.1.0",
                    )
                ],
                debate_used=True,
            )
        ],
        priority_actions=[
            PriorityAction(
                title="论证链缺少明确的验证环节",
                severity=Severity.HIGH,
                dimension=Dimension.LOGIC_CHAIN,
                why_it_matters="没有验证环节会削弱研究结论的说服力。",
                next_action="补充实验设计、评价指标和关键结果。",
                anchor_id="sec-004",
            )
        ],
        student_guidance=StudentGuidance(
            next_steps=["先把实验设计、评价指标和对比对象补完整。"]
        ),
        advisor_view=AdvisorView(
            quick_summary="当前发现 1 个高严重度问题，主要集中在论证验证环节。",
            watch_points=["研究内容：论证链缺少明确的验证环节（logic_chain）"],
        ),
        safety_notice="本系统默认处于 review mode，输出诊断与修改建议，不直接代写正文。",
        generated_at=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
    )

    output_path = tmp_path / "review.pdf"
    exporter.export(report, paper_title="PaperMentor 示例论文", output_path=output_path)

    pdf_bytes = output_path.read_bytes()

    assert output_path.exists()
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"/STSong-Light" in pdf_bytes
    assert b"/Type /Page" in pdf_bytes
