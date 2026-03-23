import json

from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _paper() -> PaperPackage:
    return PaperPackage(
        paper_id="paper-writing-llm-integration",
        title="面向本科论文初审的评审框架设计与实现",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=(
            "本文提出一套面向本科论文初审的评审框架，"
            "用于提升高优先级问题定位效率，并通过实验评估验证其效果。"
        ),
        sections=[
            Section(
                section_id="sec-1",
                heading="1 绪论",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-1",
                        anchor_id="sec-1-p-1",
                        text="本文针对本科论文初审效率不足的问题，提出一套结构化评审框架。",
                    )
                ],
            ),
            Section(
                section_id="sec-2",
                heading="2 方法设计",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-2-p-1",
                        text="框架由五个维度 worker、evidence ledger 和 selective debate 组成。",
                    )
                ],
            ),
            Section(
                section_id="sec-3",
                heading="3 实验评估",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-3",
                        anchor_id="sec-3-p-1",
                        text="实验评估围绕高严重度问题召回率、误报率和 actionability 指标展开。",
                    )
                ],
            ),
        ],
        references=[
            PaperReference(
                reference_id="ref-1",
                anchor_id="ref-1",
                raw_text="[1] Ref 1.",
            )
        ],
    )


def test_chief_reviewer_accepts_model_backed_writing_format_agent() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "结构完整，但摘要还可以更凝练。",
                    "score": 8.2,
                    "findings": [
                        {
                            "issue_title": "摘要还可以更凝练",
                            "severity": "low",
                            "confidence": 0.77,
                            "diagnosis": "摘要已包含核心信息，但表达还可以更简洁。",
                            "why_it_matters": "更凝练的摘要有助于导师快速抓住论文重点。",
                            "next_action": "压缩重复措辞，保留问题、方法和结果三类核心信息。",
                            "evidence_anchor_id": "abstract",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    writing_format_agent = WritingFormatAgent(
        llm_client=LLMClient(provider),
        llm_config=ProviderConfig(
            provider_id="fake",
            model_name="writing-format-poc",
            prompt_char_budget=5000,
        ),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    reviewer = ChiefReviewer(writing_format_agent=writing_format_agent)

    report = reviewer.review_paper(_paper())

    assert len(report.dimension_reports) == 5
    writing_report = next(item for item in report.dimension_reports if item.dimension == Dimension.WRITING_FORMAT)
    assert writing_report.summary == "结构完整，但摘要还可以更凝练。"
    assert writing_report.findings[0].issue_title == "摘要还可以更凝练"
