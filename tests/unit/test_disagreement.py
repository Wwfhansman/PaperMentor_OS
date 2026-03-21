from papermentor_os.orchestrator.disagreement import DisagreementDetector
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity


def test_disagreement_detector_flags_subjective_borderline_report() -> None:
    report = DimensionReport(
        dimension=Dimension.NOVELTY_DEPTH,
        score=6.0,
        summary="summary",
        findings=[
            ReviewFinding(
                dimension=Dimension.NOVELTY_DEPTH,
                issue_title="论文没有明确交代创新点或研究贡献",
                severity=Severity.HIGH,
                confidence=0.76,
                evidence_anchor=EvidenceAnchor(
                    anchor_id="abstract",
                    location_label="摘要",
                    quote="本文设计了一个系统。",
                ),
                diagnosis="diagnosis",
                why_it_matters="why",
                next_action="action",
                source_agent="NoveltyDepthAgent",
                source_skill_version="novelty-depth-rubric@0.1.0",
            )
        ],
        debate_used=False,
    )

    cases = DisagreementDetector().detect([report])

    assert len(cases) == 1
    assert cases[0].dimension == Dimension.NOVELTY_DEPTH
    assert cases[0].should_trigger is True


def test_disagreement_detector_ignores_non_subjective_dimension() -> None:
    report = DimensionReport(
        dimension=Dimension.WRITING_FORMAT,
        score=5.0,
        summary="summary",
        findings=[
            ReviewFinding(
                dimension=Dimension.WRITING_FORMAT,
                issue_title="摘要信息量不足",
                severity=Severity.HIGH,
                confidence=0.7,
                evidence_anchor=EvidenceAnchor(
                    anchor_id="abstract",
                    location_label="摘要",
                    quote="短摘要",
                ),
                diagnosis="diagnosis",
                why_it_matters="why",
                next_action="action",
                source_agent="WritingFormatAgent",
                source_skill_version="writing-format-rubric@0.1.0",
            )
        ],
        debate_used=False,
    )

    cases = DisagreementDetector().detect([report])

    assert cases == []

