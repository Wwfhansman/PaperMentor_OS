import json

from papermentor_os.agents.novelty_depth import NoveltyDepthAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _build_paper() -> PaperPackage:
    return PaperPackage(
        paper_id="novelty-paper-001",
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
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-1-p-2",
                        text="研究目标是提高高优先级问题定位效率，并减少自由聊天式评审的不稳定性。",
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
                        paragraph_id="p-4",
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


def _llm_config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="fake",
        model_name="novelty-depth-poc",
        prompt_char_budget=5000,
    )


def test_novelty_depth_agent_can_use_model_backend() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "创新定位存在，但贡献表达还可以再集中。",
                    "score": 7.3,
                    "findings": [
                        {
                            "issue_title": "研究贡献的归纳还不够集中",
                            "severity": "medium",
                            "confidence": 0.81,
                            "diagnosis": "当前已经表达与已有方案的差异，但贡献总结还不够集中和显式。",
                            "why_it_matters": "如果贡献表达分散，评审者会更难快速判断论文的创新价值。",
                            "next_action": "增加一段集中总结，明确列出本文相对已有方案新增或改进的 2-3 个点。",
                            "evidence_anchor_id": "abstract",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    agent = NoveltyDepthAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )

    report = agent.review(_build_paper())

    assert report.dimension == Dimension.NOVELTY_DEPTH
    assert report.summary == "创新定位存在，但贡献表达还可以再集中。"
    assert report.findings[0].issue_title == "研究贡献的归纳还不够集中"
    assert report.findings[0].evidence_anchor.anchor_id == "abstract"
    assert report.findings[0].source_skill_version == "novelty-depth-rubric@0.1.0"
    assert agent.last_model_based_report is not None


def test_novelty_depth_agent_falls_back_to_rule_backend_on_invalid_model_output() -> None:
    provider = FakeLLMProvider(responses=["not valid json"])
    agent = NoveltyDepthAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    paper = _build_paper().model_copy(
        update={
            "title": "某系统设计与实现",
            "abstract": "本文介绍系统设计与实现过程。",
            "sections": [
                Section(
                    section_id="sec-1",
                    heading="1 绪论",
                    level=1,
                    paragraphs=[
                        Paragraph(
                            paragraph_id="p-1",
                            anchor_id="sec-1-p-1",
                            text="本文完成了系统搭建和部署。",
                        )
                    ],
                )
            ],
        }
    )

    report = agent.review(paper)
    issue_titles = {finding.issue_title for finding in report.findings}

    assert "论文没有明确交代创新点或研究贡献" in issue_titles
    assert agent.last_rule_based_report is not None
    assert agent.last_model_based_report is None


def test_novelty_depth_agent_builds_compact_model_messages() -> None:
    agent = NoveltyDepthAgent(
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
    assert "sec-3-p-1" in messages[1].content
    assert len(messages[1].content) < 1700
