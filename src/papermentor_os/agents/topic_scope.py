from __future__ import annotations

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.shared.text import keyword_overlap
from papermentor_os.skills.loader import SkillBundle


GENERIC_TITLE_HINTS = ("系统", "研究", "设计", "实现", "分析", "探索")
SPECIFIC_SCOPE_HINTS = (
    "面向",
    "针对",
    "基于",
    "多智能体",
    "本科论文",
    "毕业论文",
    "初审",
    "评审",
    "反馈",
    "计算机专业",
    "框架",
    "方法",
    "检测",
    "推荐",
    "模板",
    "适配",
)
PROBLEM_HINTS = ("问题", "目标", "本文", "提出", "解决", "研究")
METHOD_HINTS = ("设计", "实现", "算法", "模型", "实验", "框架")
RESULT_HINTS = ("结果", "验证", "评估", "性能", "效果")


class TopicScopeAgent(BaseReviewAgent):
    agent_name = "TopicScopeAgent"
    skill_version = "topic-clarity-rubric@0.1.0"

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)
        abstract = paper.abstract or ""
        body_text = paper.body_text

        if not abstract:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="摘要缺失，研究问题无法快速定位",
                    diagnosis="当前论文没有可用摘要，评审者无法快速判断研究对象、方法和预期贡献。",
                    why_it_matters="摘要缺失会直接降低选题清晰度，也会让导师更难做初审判断。",
                    next_action="先补一版摘要，至少讲清研究对象、核心问题、方法路径和预期结果。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="abstract",
                        location_label="摘要",
                        quote="未识别到摘要内容。",
                    ),
                )
            )
        else:
            if not self._contains_any(abstract, PROBLEM_HINTS):
                findings.append(
                    self._finding(
                        skill_version=skill_version,
                        severity=Severity.HIGH,
                        issue_title="摘要没有明确点出研究问题",
                        diagnosis="摘要里缺少对“要解决什么问题”的直接表述，选题目标显得模糊。",
                        why_it_matters="如果问题陈述不清，后续方法、实验和结论都会缺少统一的评价基准。",
                        next_action="在摘要前半段明确写出研究对象、痛点和具体研究问题，而不是只描述做了什么系统。",
                        evidence_anchor=EvidenceAnchor(
                            anchor_id="abstract",
                            location_label="摘要",
                            quote=abstract[:120],
                        ),
                    )
                )

            missing_method = not self._contains_any(abstract, METHOD_HINTS)
            missing_result = not self._contains_any(abstract, RESULT_HINTS)
            if missing_method or missing_result:
                findings.append(
                    self._finding(
                        skill_version=skill_version,
                        severity=Severity.MEDIUM,
                        issue_title="摘要缺少方法或结果闭环",
                        diagnosis="摘要对“怎么做”或“做完得到什么”交代不足，研究闭环不够完整。",
                        why_it_matters="题目价值不仅取决于选题本身，还取决于论文是否形成了问题、方法、结果的一致链路。",
                        next_action="把摘要改成完整闭环：研究问题、方法路径、验证方式、结果结论各占一句。",
                        evidence_anchor=EvidenceAnchor(
                            anchor_id="abstract",
                            location_label="摘要",
                            quote=abstract[:120],
                        ),
                    )
                )

        overlap = keyword_overlap(paper.title, abstract)
        if abstract and overlap < 0.15 and not self._title_and_abstract_share_specific_scope(paper.title, abstract):
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="标题与摘要的一致性偏弱",
                    diagnosis="标题和摘要共享的关键术语较少，可能意味着研究对象、问题范围或方法表述没有对齐。",
                    why_it_matters="标题、摘要、正文不一致会让评审者怀疑选题边界是否稳定。",
                    next_action="检查标题是否准确覆盖摘要里的研究对象与方法，如果不匹配，优先统一研究对象和核心任务表述。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="title",
                        location_label="标题",
                        quote=paper.title,
                    ),
                )
            )

        generic_hint_count = sum(1 for token in GENERIC_TITLE_HINTS if token in paper.title)
        has_specific_scope = self._contains_any(paper.title, SPECIFIC_SCOPE_HINTS)
        if generic_hint_count >= 2 and not has_specific_scope:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="标题偏泛，范围边界不够具体",
                    diagnosis="题目里以泛化描述为主，但缺少明确的对象、场景或技术限定词。",
                    why_it_matters="题目过泛会使论文看起来像项目说明，而不是有清晰研究问题的毕业论文。",
                    next_action="把标题收窄到具体对象、技术路线或应用场景，避免只写“系统设计与实现”这类泛标题。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="title",
                        location_label="标题",
                        quote=paper.title,
                    ),
                )
            )

        if body_text and not self._contains_any(body_text[:1200], PROBLEM_HINTS):
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="正文前部未快速建立研究问题",
                    diagnosis="正文开头部分更多是在铺陈背景，但没有尽快把研究问题和论文目标立起来。",
                    why_it_matters="研究问题出现过晚，会让后续章节看起来像功能堆叠，而不是围绕问题展开的研究。",
                    next_action="在绪论或第一章前半部分明确加入“研究问题/研究目标/论文贡献”小节。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].paragraphs[0].anchor_id if paper.sections and paper.sections[0].paragraphs else "title",
                        location_label="正文前部",
                        quote=body_text[:120],
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

        summary = "选题与问题定义已经有基础表达，但研究问题边界仍需进一步收束。"
        if not findings:
            summary = "选题价值与问题清晰度维度未发现明显高优先级问题。"

        return DimensionReport(
            dimension=Dimension.TOPIC_SCOPE,
            score=score,
            summary=summary,
            findings=findings,
            debate_used=False,
        )

    def _contains_any(self, text: str, hints: tuple[str, ...]) -> bool:
        return any(hint in text for hint in hints)

    def _title_and_abstract_share_specific_scope(self, title: str, abstract: str) -> bool:
        title_hints = {hint for hint in SPECIFIC_SCOPE_HINTS if hint in title}
        if not title_hints:
            return False
        abstract_hints = {hint for hint in title_hints if hint in abstract}
        return len(abstract_hints) >= 2

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
            dimension=Dimension.TOPIC_SCOPE,
            issue_title=issue_title,
            severity=severity,
            confidence=0.78 if severity != Severity.LOW else 0.68,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
