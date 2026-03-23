import json

from papermentor_os.agents.writing_format import WritingFormatAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _build_paper() -> PaperPackage:
    return PaperPackage(
        paper_id="writing-paper-001",
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


def _llm_config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="fake",
        model_name="writing-format-poc",
        prompt_char_budget=5000,
    )


def test_writing_format_agent_can_use_model_backend() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "写作结构基本完整，但摘要表达还可以更紧凑。",
                    "score": 8.1,
                    "findings": [
                        {
                            "issue_title": "摘要表达还可以更紧凑",
                            "severity": "low",
                            "confidence": 0.79,
                            "diagnosis": "摘要已经包含问题、方法和结果，但表达还可以更凝练。",
                            "why_it_matters": "更紧凑的摘要能帮助导师更快建立整体印象。",
                            "next_action": "压缩重复修饰语，保留问题、方法、结果三类关键信息。",
                            "evidence_anchor_id": "abstract",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    agent = WritingFormatAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )

    report = agent.review(_build_paper())

    assert report.dimension == Dimension.WRITING_FORMAT
    assert report.summary == "写作结构基本完整，但摘要表达还可以更紧凑。"
    assert report.findings[0].issue_title == "摘要表达还可以更紧凑"
    assert report.findings[0].evidence_anchor.anchor_id == "abstract"
    assert report.findings[0].source_skill_version == "writing-format-rubric@0.1.0"
    assert agent.last_model_based_report is not None


def test_writing_format_agent_falls_back_to_rule_backend_on_invalid_model_output() -> None:
    provider = FakeLLMProvider(responses=["not valid json"])
    agent = WritingFormatAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    paper = _build_paper().model_copy(
        update={
            "abstract": "",
            "sections": [
                Section(
                    section_id="sec-1",
                    heading="1 绪论",
                    level=1,
                    paragraphs=[
                        Paragraph(
                            paragraph_id="p-1",
                            anchor_id="sec-1-p-1",
                            text="本文提出一套框架。",
                        )
                    ],
                )
            ],
            "references": [],
        }
    )

    report = agent.review(paper)
    issue_titles = {finding.issue_title for finding in report.findings}

    assert "章节结构不足以支撑毕业论文草稿" in issue_titles
    assert "缺少参考文献列表" in issue_titles
    assert agent.last_rule_based_report is not None
    assert agent.last_model_based_report is None


def test_writing_format_agent_builds_compact_model_messages() -> None:
    agent = WritingFormatAgent(
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
    assert len(messages[0].content) < 200
    assert messages[1].content.count('"heading"') == 3
    assert "reference_count" in messages[1].content
    assert len(messages[1].content) < 1750
