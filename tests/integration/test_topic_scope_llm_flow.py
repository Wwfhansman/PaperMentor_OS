import json

from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _paper() -> PaperPackage:
    return PaperPackage(
        paper_id="paper-llm-integration",
        title="面向本科论文初审的多智能体评审系统设计与实现",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=(
            "本文提出一套面向本科论文初审的多智能体评审系统，"
            "用于提升导师在草稿阶段的问题定位效率，并通过实验评估验证系统效果。"
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
                        text="本文针对本科论文初审反馈滞后的问题，提出一套结构化评审系统。",
                    ),
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-1-p-2",
                        text="研究目标是提高高优先级问题定位效率，并验证系统化评审流程是否优于单一 prompt 方案。",
                    ),
                ],
            ),
            Section(
                section_id="sec-2",
                heading="2 相关工作",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-3",
                        anchor_id="sec-2-p-1",
                        text="现有研究主要关注写作辅助和自动评分，对证据约束与维度化评审讨论不足。",
                    ),
                ],
            ),
            Section(
                section_id="sec-3",
                heading="3 方法设计",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-4",
                        anchor_id="sec-3-p-1",
                        text="系统由 ChiefReviewer、五个 worker、evidence ledger 和 debate judge 构成。",
                    ),
                ],
            ),
        ],
        references=[
            PaperReference(
                reference_id="ref-1",
                anchor_id="ref-1",
                raw_text="[1] Zhang. Structured Review Workflow. 2024.",
            ),
            PaperReference(
                reference_id="ref-2",
                anchor_id="ref-2",
                raw_text="[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
            ),
        ],
    )


def test_chief_reviewer_accepts_model_backed_topic_scope_agent() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "选题与摘要基本对齐，但研究问题还可以再聚焦。",
                    "score": 7.8,
                    "findings": [
                        {
                            "issue_title": "研究问题的表述还可以再聚焦",
                            "severity": "medium",
                            "confidence": 0.84,
                            "diagnosis": "摘要和绪论都说明了系统目标，但研究问题的边界还可以更紧凑。",
                            "why_it_matters": "问题边界收束得更清楚，后续方法和实验评价标准才会更稳定。",
                            "next_action": "在摘要和绪论中统一使用一句更直接的研究问题表述。",
                            "evidence_anchor_id": "abstract",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    topic_scope_agent = TopicScopeAgent(
        llm_client=LLMClient(provider),
        llm_config=ProviderConfig(
            provider_id="fake",
            model_name="topic-scope-poc",
            prompt_char_budget=4000,
        ),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    reviewer = ChiefReviewer(topic_scope_agent=topic_scope_agent)

    report = reviewer.review_paper(_paper())

    assert len(report.dimension_reports) == 5
    topic_report = next(item for item in report.dimension_reports if item.dimension == Dimension.TOPIC_SCOPE)
    assert topic_report.summary == "选题与摘要基本对齐，但研究问题还可以再聚焦。"
    assert topic_report.findings[0].issue_title == "研究问题的表述还可以再聚焦"
    assert report.priority_actions[0].dimension != Dimension.WRITING_FORMAT
