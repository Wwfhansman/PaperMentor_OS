from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.llm import (
    LLMClient,
    LLMConfigurationError,
    LLMError,
    LLMMessage,
    MessageRole,
    ProviderConfig,
    ReviewBackend,
)
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.trace import WorkerExecutionMetadata
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle


NOVELTY_HINTS = ("创新", "novel", "new", "改进", "提出", "贡献")
LIMITATION_HINTS = ("局限", "不足", "future work", "后续工作")
DEPTH_HINTS = ("实验", "评估", "分析", "对比", "消融", "ablation")
SYSTEM_ONLY_HINTS = ("设计与实现", "系统实现", "系统设计", "平台搭建")
CONTRIBUTION_COMPARISON_HINTS = ("相较", "相对于", "优于", "区别于", "差异", "定位", "相比")
MODEL_ABSTRACT_LIMIT = 260
MODEL_SECTION_COUNT = 3
MODEL_SECTION_PARAGRAPH_COUNT = 1
MODEL_PARAGRAPH_LIMIT = 130
MODEL_ANCHOR_QUOTE_LIMIT = 90
MODEL_RUBRIC_LIMIT = 650
MODEL_POLICY_LIMIT = 450
MODEL_DOMAIN_LIMIT = 350


class NoveltyDepthLLMFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_title: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    diagnosis: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    evidence_anchor_id: str = Field(min_length=1)


class NoveltyDepthLLMOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=10.0)
    findings: list[NoveltyDepthLLMFinding] = Field(default_factory=list)


class NoveltyDepthAgent(BaseReviewAgent):
    agent_name = "NoveltyDepthAgent"
    skill_version = "novelty-depth-rubric@0.1.0"

    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        llm_config: ProviderConfig | None = None,
        review_backend: ReviewBackend = ReviewBackend.RULE_ONLY,
    ) -> None:
        self.llm_client = llm_client
        self.llm_config = llm_config
        self.review_backend = review_backend
        self.last_rule_based_report: DimensionReport | None = None
        self.last_model_based_report: DimensionReport | None = None
        self.last_effective_backend = ReviewBackend.RULE_ONLY.value
        self.last_structured_output_status = "not_requested"
        self.last_fallback_used = False
        self.last_llm_provider_id: str | None = None
        self.last_llm_model_name: str | None = None
        self.last_llm_finish_reason: str | None = None
        self.last_llm_error_category: str | None = None
        self.last_llm_runtime_stats = None

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        rule_report = self._review_rule_based(paper, skill_bundle)
        self.last_rule_based_report = rule_report
        self.last_model_based_report = None
        self.last_effective_backend = self.review_backend.value
        self.last_structured_output_status = "not_requested"
        self.last_fallback_used = False
        self.last_llm_provider_id = self.llm_config.provider_id if self.llm_config is not None else None
        self.last_llm_model_name = self.llm_config.model_name if self.llm_config is not None else None
        self.last_llm_finish_reason = None
        self.last_llm_error_category = None
        self.last_llm_runtime_stats = None

        if self.review_backend == ReviewBackend.RULE_ONLY:
            return rule_report

        if self.llm_client is None or self.llm_config is None:
            self.last_structured_output_status = "configuration_error"
            raise LLMConfigurationError(
                "NoveltyDepthAgent model review requires llm_client and llm_config."
            )

        try:
            model_report = self._review_with_llm(paper, skill_bundle)
        except LLMError as error:
            self.capture_llm_runtime_stats(error.runtime_stats)
            self.last_structured_output_status = self.classify_llm_error(error)
            self.last_llm_error_category = self.categorize_llm_error(error)
            if self.review_backend == ReviewBackend.MODEL_WITH_FALLBACK:
                self.last_fallback_used = True
                return rule_report
            raise

        self.last_model_based_report = model_report
        return model_report

    def _review_rule_based(
        self,
        paper: PaperPackage,
        skill_bundle: SkillBundle | None = None,
    ) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)
        abstract = paper.abstract or ""
        body_text = paper.body_text
        heading_text = " ".join(section.heading for section in paper.sections)
        combined_text = " ".join((paper.title, abstract, body_text[:2000]))

        mentions_novelty = self._contains_any(combined_text, NOVELTY_HINTS)
        has_depth_signals = self._contains_any(combined_text, DEPTH_HINTS)
        has_limitations = self._contains_any(combined_text, LIMITATION_HINTS)
        system_only_title = self._contains_any(paper.title, SYSTEM_ONLY_HINTS)
        expresses_comparative_contribution = self._contains_any(combined_text, CONTRIBUTION_COMPARISON_HINTS)
        has_contribution_expression = mentions_novelty or (
            expresses_comparative_contribution and has_depth_signals
        )

        if not has_contribution_expression:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="论文没有明确交代创新点或研究贡献",
                    diagnosis="当前标题、摘要和正文前部没有清楚说明论文相对已有工作的新增价值或研究贡献。",
                    why_it_matters="如果创新点不明确，评审者会更倾向于把论文理解为普通项目总结，而不是研究型毕业论文。",
                    next_action="单独增加“创新点/贡献”表述，明确说明本文相对已有方法新增了什么、改善了什么、解决了什么限制。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="abstract" if abstract else "title",
                        location_label="标题与摘要",
                        quote=abstract[:120] if abstract else paper.title,
                    ),
                )
            )

        if system_only_title and not has_depth_signals:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="论文更像系统实现说明，研究深度不足",
                    diagnosis="题目和正文更强调系统设计与实现，但缺少方法比较、机制分析或深入验证，研究深度偏弱。",
                    why_it_matters="V1 目标是本科毕业论文评审，不是单纯验收功能实现；没有研究深度会直接影响创新性判断。",
                    next_action="补充方法选择依据、关键设计权衡、实验比较或误差分析，把工作从“做出来”推进到“论证清楚为什么这样做”。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="title",
                        location_label="标题",
                        quote=paper.title,
                    ),
                )
            )

        if has_contribution_expression and not has_depth_signals:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="宣称有创新，但缺少足够研究深度支撑",
                    diagnosis="论文中存在创新或改进表述，但缺少实验、分析或对比来支撑这些主张。",
                    why_it_matters="创新性判断不能只靠口头声明，必须通过方法分析和验证过程建立可信度。",
                    next_action="把创新点逐条对应到实验结果、对比分析或机制解释，避免只在摘要里声明“有创新”。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].paragraphs[0].anchor_id if paper.sections and paper.sections[0].paragraphs else "title",
                        location_label="正文前部",
                        quote=body_text[:120] or paper.title,
                    ),
                )
            )

        if not has_limitations:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.LOW,
                    issue_title="缺少局限性或后续工作反思",
                    diagnosis="正文中没有明显讨论当前方案的局限、适用边界或后续工作方向。",
                    why_it_matters="对局限性的主动说明能提高研究表达的成熟度，也有助于导师判断作者是否真正理解自己的工作边界。",
                    next_action="在结论中补充局限性和后续工作，说明当前方案在哪些条件下仍然不足。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[-1].section_id if paper.sections else "title",
                        location_label="结尾部分",
                        quote=heading_text.split()[-1] if heading_text else paper.title,
                    ),
                )
            )

        score = 8.0
        for finding in findings:
            if finding.severity == Severity.HIGH:
                score -= 2.0
            elif finding.severity == Severity.MEDIUM:
                score -= 1.0
            else:
                score -= 0.5
        score = max(score, 1.0)

        summary = "创新性与研究深度已有初步表达，但还需要更清晰的贡献界定和深度支撑。"
        if not findings:
            summary = "创新性与研究深度维度未发现明显高优先级问题。"

        return DimensionReport(
            dimension=Dimension.NOVELTY_DEPTH,
            score=score,
            summary=summary,
            findings=findings,
            debate_used=False,
        )

    def _review_with_llm(
        self,
        paper: PaperPackage,
        skill_bundle: SkillBundle | None = None,
    ) -> DimensionReport:
        if self.llm_client is None or self.llm_config is None:
            raise LLMConfigurationError(
                "NoveltyDepthAgent model review requires llm_client and llm_config."
            )

        skill_version = self.resolve_skill_version(skill_bundle)
        anchor_map = self._build_anchor_map(paper)
        structured_response = self.llm_client.generate_structured(
            self._build_model_messages(paper, skill_bundle, anchor_map),
            NoveltyDepthLLMOutput,
            self.llm_config,
        )
        self.last_structured_output_status = "parsed"
        self.last_llm_provider_id = structured_response.raw.provider_id
        self.last_llm_model_name = structured_response.raw.model_name
        self.last_llm_finish_reason = structured_response.raw.finish_reason
        self.last_llm_error_category = None
        self.capture_llm_runtime_stats(structured_response.raw.runtime_stats)

        findings: list[ReviewFinding] = []
        for finding in structured_response.parsed.findings:
            anchor = anchor_map.get(finding.evidence_anchor_id)
            if anchor is None:
                raise LLMConfigurationError(
                    f"NoveltyDepthAgent received unknown evidence anchor '{finding.evidence_anchor_id}'."
                )
            findings.append(
                ReviewFinding(
                    dimension=Dimension.NOVELTY_DEPTH,
                    issue_title=finding.issue_title,
                    severity=finding.severity,
                    confidence=finding.confidence,
                    evidence_anchor=anchor,
                    diagnosis=finding.diagnosis,
                    why_it_matters=finding.why_it_matters,
                    next_action=finding.next_action,
                    source_agent=self.agent_name,
                    source_skill_version=skill_version,
                )
            )

        return DimensionReport(
            dimension=Dimension.NOVELTY_DEPTH,
            score=structured_response.parsed.score,
            summary=structured_response.parsed.summary,
            findings=findings,
            debate_used=False,
        )

    def _build_model_messages(
        self,
        paper: PaperPackage,
        skill_bundle: SkillBundle | None,
        anchor_map: dict[str, EvidenceAnchor],
    ) -> list[LLMMessage]:
        rubric_text = self._truncate_text(
            "\n".join(
                skill.body for skill in (skill_bundle.rubric_skills if skill_bundle else []) if skill.body
            ),
            MODEL_RUBRIC_LIMIT,
        )
        policy_text = self._truncate_text(
            "\n".join(
                skill.body for skill in (skill_bundle.policy_skills if skill_bundle else []) if skill.body
            ),
            MODEL_POLICY_LIMIT,
        )
        domain_text = self._truncate_text(
            "\n".join(
                skill.body for skill in (skill_bundle.domain_skills if skill_bundle else []) if skill.body
            ),
            MODEL_DOMAIN_LIMIT,
        )

        prompt_payload = {
            "paper": {
                "title": paper.title,
                "abstract": self._truncate_text(
                    paper.abstract or "未识别到摘要内容。",
                    MODEL_ABSTRACT_LIMIT,
                ),
                "sections": [
                    {
                        "heading": section.heading,
                        "paragraphs": [
                            {
                                "anchor_id": paragraph.anchor_id,
                                "text": self._truncate_text(paragraph.text, MODEL_PARAGRAPH_LIMIT),
                            }
                            for paragraph in section.paragraphs[:MODEL_SECTION_PARAGRAPH_COUNT]
                        ],
                    }
                    for section in paper.sections[:MODEL_SECTION_COUNT]
                ],
            },
            "allowed_anchors": [
                {
                    "anchor_id": anchor.anchor_id,
                    "location_label": anchor.location_label,
                    "quote": self._truncate_text(anchor.quote, MODEL_ANCHOR_QUOTE_LIMIT),
                }
                for anchor in anchor_map.values()
            ],
        }
        if rubric_text:
            prompt_payload["rubric"] = rubric_text
        if policy_text:
            prompt_payload["policies"] = policy_text
        if domain_text:
            prompt_payload["domain_rules"] = domain_text

        return [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "你是 PaperMentor OS 的 NoveltyDepthAgent。"
                    "只评估“创新性与研究深度”维度，不要扩展到其他维度。"
                    "优先检查贡献表达是否清楚、研究深度是否足够以及是否有局限性反思。"
                    "不要输出代写内容，所有 finding 都必须引用给定的 evidence_anchor_id。"
                    "保持输出精炼，只根据摘要和关键章节判断贡献定位与研究深度。"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=(
                    "请基于以下论文上下文输出结构化评审结果。"
                    "如果没有明显问题，findings 可为空，但 summary 和 score 仍必须给出。\n"
                    f"{json.dumps(prompt_payload, ensure_ascii=False, separators=(',', ':'))}"
                ),
            ),
        ]

    def _build_anchor_map(self, paper: PaperPackage) -> dict[str, EvidenceAnchor]:
        anchors: dict[str, EvidenceAnchor] = {
            "title": EvidenceAnchor(
                anchor_id="title",
                location_label="标题",
                quote=paper.title,
            ),
            "abstract": EvidenceAnchor(
                anchor_id="abstract",
                location_label="摘要",
                quote=paper.abstract or "未识别到摘要内容。",
            ),
        }
        for section in paper.sections[:MODEL_SECTION_COUNT]:
            anchors[section.section_id] = EvidenceAnchor(
                anchor_id=section.section_id,
                location_label="章节结构",
                quote=section.heading,
            )
            for paragraph in section.paragraphs[:MODEL_SECTION_PARAGRAPH_COUNT]:
                anchors[paragraph.anchor_id] = EvidenceAnchor(
                    anchor_id=paragraph.anchor_id,
                    location_label=section.heading,
                    quote=paragraph.text[:160],
                )
        return anchors

    def _truncate_text(self, text: str, limit: int) -> str:
        normalized = " ".join(text.split())
        if limit <= 0 or len(normalized) <= limit:
            return normalized
        return normalized[: max(limit - 1, 0)].rstrip() + "…"

    def build_execution_metadata(self) -> WorkerExecutionMetadata:
        return self.build_llm_execution_metadata()

    def _contains_any(self, text: str, hints: tuple[str, ...]) -> bool:
        lowered = text.lower()
        return any(hint.lower() in lowered for hint in hints)

    def _finding(
        self,
        *,
        skill_version: str,
        severity: Severity,
        issue_title: str,
        diagnosis: str,
        why_it_matters: str,
        next_action: str,
        evidence_anchor: EvidenceAnchor,
    ) -> ReviewFinding:
        return ReviewFinding(
            dimension=Dimension.NOVELTY_DEPTH,
            issue_title=issue_title,
            severity=severity,
            confidence=0.76 if severity == Severity.HIGH else 0.7,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
