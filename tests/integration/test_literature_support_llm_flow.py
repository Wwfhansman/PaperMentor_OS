import json

from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _paper() -> PaperPackage:
    return PaperPackage(
        paper_id="paper-literature-llm-integration",
        title="面向本科论文初审的文献支撑审查框架设计",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=(
            "本文提出一套面向本科论文初审的文献支撑审查框架，"
            "用于分析相关工作覆盖、正文引用和方法比较是否充分。"
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
                        text="现有研究主要关注写作辅助和自动评分，但对证据约束和结构化评审讨论不足。[1]",
                    ),
                ],
            ),
            Section(
                section_id="sec-2",
                heading="2 相关工作",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-2-p-1",
                        text="本文对比已有多智能体评审方案、写作辅助工具和 benchmark 体系，并分析各自局限。[1][2][3]",
                    ),
                ],
            ),
            Section(
                section_id="sec-3",
                heading="3 方法设计",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-3",
                        anchor_id="sec-3-p-1",
                        text="系统结合 evidence ledger 与 benchmark，对已有方案做差异化比较和定位。",
                    ),
                ],
            ),
        ],
        references=[
            PaperReference(
                reference_id=f"ref-{index}",
                anchor_id=f"ref-{index}",
                raw_text=f"[{index}] Ref {index}.",
            )
            for index in range(1, 7)
        ],
    )


def test_chief_reviewer_accepts_model_backed_literature_support_agent() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "文献覆盖基本成立，但与主要基线的比较还可以更聚焦。",
                    "score": 7.8,
                    "findings": [
                        {
                            "issue_title": "与主要基线的比较还不够聚焦",
                            "severity": "medium",
                            "confidence": 0.84,
                            "diagnosis": "当前已经呈现相关工作和比较意识，但对核心基线的归纳还不够集中。",
                            "why_it_matters": "如果缺少聚焦的比较，评审者很难快速判断本文方案相对已有方法的定位。",
                            "next_action": "补一段面向主要基线的集中比较，说明方法差异、适用场景和局限。",
                            "evidence_anchor_id": "sec-2-p-1",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    literature_support_agent = LiteratureSupportAgent(
        llm_client=LLMClient(provider),
        llm_config=ProviderConfig(
            provider_id="fake",
            model_name="literature-support-poc",
            prompt_char_budget=5000,
        ),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    reviewer = ChiefReviewer(literature_support_agent=literature_support_agent)

    report = reviewer.review_paper(_paper())

    assert len(report.dimension_reports) == 5
    literature_report = next(
        item for item in report.dimension_reports if item.dimension == Dimension.LITERATURE_SUPPORT
    )
    assert literature_report.summary == "文献覆盖基本成立，但与主要基线的比较还可以更聚焦。"
    assert literature_report.findings[0].issue_title == "与主要基线的比较还不够聚焦"
