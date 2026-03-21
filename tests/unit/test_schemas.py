from papermentor_os.schemas.paper import PaperPackage, Paragraph, Section
from papermentor_os.schemas.report import AdvisorView, FinalReport, StudentGuidance
from papermentor_os.schemas.types import Discipline, PaperStage


def test_paper_package_body_text() -> None:
    paper = PaperPackage(
        paper_id="demo",
        title="demo title",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract="demo abstract",
        sections=[
            Section(
                section_id="sec-001",
                heading="1 绪论",
                level=1,
                paragraphs=[
                    Paragraph(paragraph_id="p-0001", anchor_id="sec-001-p-001", text="alpha"),
                    Paragraph(paragraph_id="p-0002", anchor_id="sec-001-p-002", text="beta"),
                ],
            )
        ],
    )

    assert paper.body_text == "alpha\nbeta"


def test_final_report_accepts_minimum_contract() -> None:
    report = FinalReport(
        overall_summary="summary",
        dimension_reports=[],
        priority_actions=[],
        student_guidance=StudentGuidance(next_steps=["step"]),
        advisor_view=AdvisorView(quick_summary="quick", watch_points=[]),
        safety_notice="notice",
    )

    assert report.safety_notice == "notice"

