import json

from papermentor_os.agents.logic_chain import LogicChainAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _build_paper() -> PaperPackage:
    return PaperPackage(
        paper_id="logic-paper-001",
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
            )
        ],
    )


def _llm_config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="fake",
        model_name="logic-chain-poc",
        prompt_char_budget=5000,
    )


def test_logic_chain_agent_can_use_model_backend() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "论证主线存在，但结论回收还可以更集中。",
                    "score": 7.4,
                    "findings": [
                        {
                            "issue_title": "结论对研究问题的回收还不够集中",
                            "severity": "medium",
                            "confidence": 0.83,
                            "diagnosis": "当前结构已经包含问题、方法和实验，但对最终回答研究问题的总结还不够集中。",
                            "why_it_matters": "如果结论不能明确回收研究问题，前面的论证价值就难以被完整呈现。",
                            "next_action": "在结论部分用一段集中回收研究问题、关键结果和适用边界。",
                            "evidence_anchor_id": "sec-3",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    agent = LogicChainAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )

    report = agent.review(_build_paper())

    assert report.dimension == Dimension.LOGIC_CHAIN
    assert report.summary == "论证主线存在，但结论回收还可以更集中。"
    assert report.findings[0].issue_title == "结论对研究问题的回收还不够集中"
    assert report.findings[0].evidence_anchor.anchor_id == "sec-3"
    assert report.findings[0].source_skill_version == "logic-chain-rubric@0.1.0"
    assert agent.last_model_based_report is not None


def test_logic_chain_agent_falls_back_to_rule_backend_on_invalid_model_output() -> None:
    provider = FakeLLMProvider(responses=["not valid json"])
    agent = LogicChainAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )

    paper = _build_paper().model_copy(
        update={
            "sections": [
                Section(
                    section_id="sec-1",
                    heading="1 绪论",
                    level=1,
                    paragraphs=[
                        Paragraph(
                            paragraph_id="p-1",
                            anchor_id="sec-1-p-1",
                            text="本文提出一套框架，并显著提升了评审效率。",
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
                            text="框架聚焦章节结构分析和问题定位。",
                        )
                    ],
                ),
            ]
        }
    )

    report = agent.review(paper)
    issue_titles = {finding.issue_title for finding in report.findings}

    assert "论证链缺少明确的验证环节" in issue_titles
    assert agent.last_rule_based_report is not None
    assert agent.last_model_based_report is None


def test_logic_chain_agent_builds_compact_model_messages() -> None:
    agent = LogicChainAgent(
        llm_client=LLMClient(FakeLLMProvider()),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )
    paper = _build_paper().model_copy(
        update={
            "abstract": _build_paper().abstract * 12,
        }
    )

    messages = agent._build_model_messages(paper, None, agent._build_anchor_map(paper))

    assert len(messages) == 2
    assert len(messages[0].content) < 190
    assert messages[1].content.count('"heading"') == 3
    assert "sec-3-p-1" in messages[1].content
    assert len(messages[1].content) < 1700
