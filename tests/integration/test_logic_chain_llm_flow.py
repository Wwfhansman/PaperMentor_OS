import json

from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _paper() -> PaperPackage:
    return PaperPackage(
        paper_id="paper-logic-llm-integration",
        title="面向本科论文初审的论证链审查框架设计",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=(
            "本文提出一套面向本科论文初审的论证链审查框架，"
            "用于识别研究问题、方法、验证和结论之间的断裂。"
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
                        text="本文针对本科论文草稿中论证链常出现断裂的问题，提出一套审查框架。",
                    ),
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-1-p-2",
                        text="研究目标是分析 claim 与 evidence 的对应关系，并提高高优先级问题定位效率。",
                    ),
                ],
            ),
            Section(
                section_id="sec-2",
                heading="2 方法设计",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-3",
                        anchor_id="sec-2-p-1",
                        text="该框架围绕研究问题、关键论断、实验设计和结果解释构建审查流程。",
                    ),
                ],
            ),
            Section(
                section_id="sec-3",
                heading="3 实验评估",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-4",
                        anchor_id="sec-3-p-1",
                        text="实验评估基于四组论文草稿，指标包括高严重度问题召回率和误报率。",
                    ),
                ],
            ),
        ],
        references=[
            PaperReference(
                reference_id="ref-1",
                anchor_id="ref-1",
                raw_text="[1] Zhang. Logic Review Workflow. 2024.",
            ),
            PaperReference(
                reference_id="ref-2",
                anchor_id="ref-2",
                raw_text="[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
            ),
        ],
    )


def test_chief_reviewer_accepts_model_backed_logic_chain_agent() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "论证链基本连贯，但结论回收还可以更明确。",
                    "score": 7.7,
                    "findings": [
                        {
                            "issue_title": "结论对关键论断的回收还不够明确",
                            "severity": "medium",
                            "confidence": 0.82,
                            "diagnosis": "问题、方法和实验已经出现，但最终如何回答研究问题的回收还不够集中。",
                            "why_it_matters": "如果结论不明确回收关键论断，整条论证链就会显得收束不足。",
                            "next_action": "在结论章节集中总结研究问题、实验结果和最终判断。",
                            "evidence_anchor_id": "sec-3-p-1",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    logic_chain_agent = LogicChainAgent(
        llm_client=LLMClient(provider),
        llm_config=ProviderConfig(
            provider_id="fake",
            model_name="logic-chain-poc",
            prompt_char_budget=5000,
        ),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    reviewer = ChiefReviewer(logic_chain_agent=logic_chain_agent)

    report = reviewer.review_paper(_paper())

    assert len(report.dimension_reports) == 5
    logic_report = next(item for item in report.dimension_reports if item.dimension == Dimension.LOGIC_CHAIN)
    assert logic_report.summary == "论证链基本连贯，但结论回收还可以更明确。"
    assert logic_report.findings[0].issue_title == "结论对关键论断的回收还不够明确"
