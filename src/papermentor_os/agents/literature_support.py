from __future__ import annotations

import json
import re

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


CITATION_PATTERN = re.compile(r"\[(\d+)\]|（[^）]*\d{4}[^）]*）|\([^)]*\d{4}[^)]*\)")
RELATED_WORK_HINTS = (
    "相关工作",
    "文献综述",
    "研究现状",
    "related work",
    "literature review",
    "已有方法",
    "方法比较",
    "对比分析",
)
BASELINE_HINTS = ("baseline", "对比", "比较", "benchmark", "sota")
MODEL_ABSTRACT_LIMIT = 260
MODEL_REFERENCE_PREVIEW_COUNT = 2
MODEL_REFERENCE_TEXT_LIMIT = 45
MODEL_SECTION_COUNT = 2
MODEL_SECTION_PARAGRAPH_COUNT = 1
MODEL_PARAGRAPH_LIMIT = 130
MODEL_ANCHOR_QUOTE_LIMIT = 90
MODEL_RUBRIC_LIMIT = 650
MODEL_POLICY_LIMIT = 450
MODEL_DOMAIN_LIMIT = 350


class LiteratureSupportLLMFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_title: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    diagnosis: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    evidence_anchor_id: str = Field(min_length=1)


class LiteratureSupportLLMOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=10.0)
    findings: list[LiteratureSupportLLMFinding] = Field(default_factory=list)


class LiteratureSupportAgent(BaseReviewAgent):
    agent_name = "LiteratureSupportAgent"
    skill_version = "literature-support-rubric@0.1.0"

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
                "LiteratureSupportAgent model review requires llm_client and llm_config."
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
        body_text = paper.body_text
        section_headings = [section.heading for section in paper.sections]
        has_related_work = self._contains_any(" ".join(section_headings), RELATED_WORK_HINTS)
        citation_count = len(CITATION_PATTERN.findall(body_text))
        reference_count = len(paper.references)
        has_baseline_discussion = self._contains_any(body_text, BASELINE_HINTS)

        if reference_count < 5:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="参考文献数量偏少，难以支撑毕业论文评审",
                    diagnosis="当前识别到的参考文献数量较少，文献基础看起来还不足以支撑完整的相关工作分析。",
                    why_it_matters="文献支撑不足会直接影响选题价值判断、方法对比和创新性论证。",
                    next_action="优先补充与研究问题直接相关的核心论文、方法对比文献和近年代表性工作，再重写相关工作部分。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="参考文献",
                        quote=f"当前仅识别到 {reference_count} 条参考文献。",
                    ),
                )
            )

        if not has_related_work:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="缺少显式相关工作或文献综述部分",
                    diagnosis="章节结构中没有清晰的相关工作、文献综述或研究现状部分，文献梳理不够显式。",
                    why_it_matters="没有专门的文献支撑章节，会让评审者难以判断论文是否完成了必要的领域定位。",
                    next_action="增加“相关工作”或“研究现状”小节，按研究方向或方法类别梳理已有工作与论文定位。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].section_id if paper.sections else "title",
                        location_label="章节结构",
                        quote="未识别到相关工作/文献综述类章节标题。",
                    ),
                )
            )

        if reference_count > 0 and citation_count == 0:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="正文缺少显式引用，文献没有进入论证链路",
                    diagnosis="虽然存在参考文献列表，但正文中没有识别到稳定的引用痕迹，文献未真正参与论证。",
                    why_it_matters="文献如果只出现在文末而不进入正文论证，就无法支撑问题定义、方法选择和结果比较。",
                    next_action="在问题背景、方法选择和结果比较处补充明确引用，让关键论断都能回到文献来源。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="正文与参考文献关系",
                        quote="识别到参考文献列表，但正文未识别到引用标记。",
                    ),
                )
            )

        if not has_baseline_discussion:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="缺少与已有方法或基线的比较意识",
                    diagnosis="正文没有明显讨论已有方法、对比对象或 benchmark，文献支撑更像罗列而不是比较分析。",
                    why_it_matters="计算机专业本科毕业论文通常需要说明自己的方法相对已有方案的定位和差异。",
                    next_action="在相关工作或实验分析中补充对比基线，说明已有方法做法、局限以及本文方案的差异点。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].paragraphs[0].anchor_id if paper.sections and paper.sections[0].paragraphs else "title",
                        location_label="正文分析",
                        quote=body_text[:120] or paper.title,
                    ),
                )
            )

        score = 8.5
        for finding in findings:
            if finding.severity == Severity.HIGH:
                score -= 2.0
            elif finding.severity == Severity.MEDIUM:
                score -= 1.0
            else:
                score -= 0.5
        score = max(score, 1.0)

        summary = "文献支撑有基础框架，但相关工作梳理和引用进入论证链的程度仍然不足。"
        if not findings:
            summary = "文献支撑维度未发现明显高优先级问题。"

        return DimensionReport(
            dimension=Dimension.LITERATURE_SUPPORT,
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
                "LiteratureSupportAgent model review requires llm_client and llm_config."
            )

        skill_version = self.resolve_skill_version(skill_bundle)
        anchor_map = self._build_anchor_map(paper)
        structured_response = self.llm_client.generate_structured(
            self._build_model_messages(paper, skill_bundle, anchor_map),
            LiteratureSupportLLMOutput,
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
                    f"LiteratureSupportAgent received unknown evidence anchor '{finding.evidence_anchor_id}'."
                )
            findings.append(
                ReviewFinding(
                    dimension=Dimension.LITERATURE_SUPPORT,
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
            dimension=Dimension.LITERATURE_SUPPORT,
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
                "reference_count": len(paper.references),
                "references_preview": [
                    self._truncate_text(reference.raw_text, MODEL_REFERENCE_TEXT_LIMIT)
                    for reference in paper.references[:MODEL_REFERENCE_PREVIEW_COUNT]
                ],
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
                    "你是 PaperMentor OS 的 LiteratureSupportAgent。"
                    "只评估“文献支撑”维度，不要扩展到其他维度。"
                    "优先检查相关工作覆盖、正文引用是否进入论证链以及是否有基线比较意识。"
                    "不要输出代写内容，所有 finding 都必须引用给定的 evidence_anchor_id。"
                    "保持输出精炼，只根据摘要、相关工作和方法前部判断文献支撑质量。"
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
            "references": EvidenceAnchor(
                anchor_id="references",
                location_label="参考文献",
                quote=f"当前识别到 {len(paper.references)} 条参考文献。",
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
            dimension=Dimension.LITERATURE_SUPPORT,
            issue_title=issue_title,
            severity=severity,
            confidence=0.82 if severity == Severity.HIGH else 0.74,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
