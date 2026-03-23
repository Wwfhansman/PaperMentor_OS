import json

from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _paper() -> PaperPackage:
    return PaperPackage(
        paper_id="paper-novelty-llm-integration",
        title="面向本科论文初审的多智能体评审框架设计与实现",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=(
            "本文提出一套面向本科论文初审的多智能体评审框架，"
            "用于提升高优先级问题识别效率，并分析其相对已有方案的差异。"
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
                        text="本文相较于已有写作辅助系统，更强调固定维度评审和证据约束。",
                    ),
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
                        text="框架由 ChiefReviewer、五个 worker、evidence ledger 和 selective debate 组成。",
                    ),
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
                    ),
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


def test_chief_reviewer_accepts_model_backed_novelty_depth_agent() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "创新方向存在，但贡献总结还可以更收束。",
                    "score": 7.6,
                    "findings": [
                        {
                            "issue_title": "贡献总结还不够收束",
                            "severity": "medium",
                            "confidence": 0.82,
                            "diagnosis": "当前已经说明与已有方案的差异，但贡献归纳还不够集中。",
                            "why_it_matters": "如果创新点散落在正文中，评审者会更难快速形成稳定判断。",
                            "next_action": "增加一段集中列出贡献点，说明每一点相较已有方案解决了什么问题。",
                            "evidence_anchor_id": "sec-1-p-1",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    novelty_depth_agent = NoveltyDepthAgent(
        llm_client=LLMClient(provider),
        llm_config=ProviderConfig(
            provider_id="fake",
            model_name="novelty-depth-poc",
            prompt_char_budget=5000,
        ),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    reviewer = ChiefReviewer(novelty_depth_agent=novelty_depth_agent)

    report = reviewer.review_paper(_paper())

    assert len(report.dimension_reports) == 5
    novelty_report = next(item for item in report.dimension_reports if item.dimension == Dimension.NOVELTY_DEPTH)
    assert novelty_report.summary == "创新方向存在，但贡献总结还可以更收束。"
    assert novelty_report.findings[0].issue_title == "贡献总结还不够收束"
