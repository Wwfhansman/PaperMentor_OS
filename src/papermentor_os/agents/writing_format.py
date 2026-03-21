from __future__ import annotations

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.schemas.paper import PaperPackage, Paragraph
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle


class WritingFormatAgent(BaseReviewAgent):
    agent_name = "WritingFormatAgent"
    skill_version = "writing-format-rubric@0.1.0"

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)

        if len(paper.sections) < 3:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="章节结构不足以支撑毕业论文草稿",
                    diagnosis="当前正文章节数量偏少，结构看起来还不像一篇已进入草稿阶段的完整毕业论文。",
                    why_it_matters="章节骨架不完整会直接影响导师对研究设计、实验安排和结论完整性的判断。",
                    next_action="先补齐至少“问题背景/方法设计/实验或实现/结论”这类核心章节，再进入细节润色。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].section_id if paper.sections else "title",
                        location_label="论文整体结构",
                        quote=f"当前仅识别到 {len(paper.sections)} 个正文章节。",
                    ),
                )
            )

        abstract_length = len(paper.abstract.replace(" ", ""))
        if abstract_length < 120:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="摘要信息量不足",
                    diagnosis="摘要篇幅较短，难以同时交代研究问题、方法与结果。",
                    why_it_matters="摘要是导师和评审快速判断论文成熟度的入口，信息不完整会削弱整体可信度。",
                    next_action="把摘要补成“问题背景-方法-结果/结论”的三段式或紧凑四句式表达。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="abstract",
                        location_label="摘要",
                        quote=paper.abstract or "摘要内容缺失",
                    ),
                )
            )

        if not paper.references:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="缺少参考文献列表",
                    diagnosis="解析结果中未识别到参考文献部分。",
                    why_it_matters="没有参考文献会让论文在学术规范和文献支撑两方面同时失分。",
                    next_action="补充规范的参考文献章节，并确保正文中的关键论断可以追溯到文献来源。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="参考文献",
                        quote="未识别到参考文献条目。",
                    ),
                )
            )

        longest_paragraph = self._find_longest_paragraph(paper)
        if longest_paragraph and len(longest_paragraph.text) > 240:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.LOW,
                    issue_title="存在过长段落，影响可读性",
                    diagnosis="部分段落信息密度高且缺少拆分，阅读时不易快速定位主句与支撑句。",
                    why_it_matters="过长段落会增加阅读负担，也会掩盖真正重要的论证节点。",
                    next_action="将长段落拆成“结论句 + 解释句 + 证据句”结构，并给关键论点单独成段。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=longest_paragraph.anchor_id,
                        location_label="正文段落",
                        quote=longest_paragraph.text[:120],
                    ),
                )
            )

        score = 9.0
        for finding in findings:
            if finding.severity == Severity.HIGH:
                score -= 2.0
            elif finding.severity == Severity.MEDIUM:
                score -= 1.0
            else:
                score -= 0.5
        score = max(score, 1.0)

        summary = "写作与格式总体可读，但仍存在影响评审效率的规范性问题。"
        if not findings:
            summary = "写作与格式维度未发现明显的高优先级问题，结构基础较完整。"

        return DimensionReport(
            dimension=Dimension.WRITING_FORMAT,
            score=score,
            summary=summary,
            findings=findings,
            debate_used=False,
        )

    def _find_longest_paragraph(self, paper: PaperPackage) -> Paragraph | None:
        paragraphs = list(paper.iter_body_paragraphs())
        if not paragraphs:
            return None
        return max(paragraphs, key=lambda paragraph: len(paragraph.text))

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
            dimension=Dimension.WRITING_FORMAT,
            issue_title=issue_title,
            severity=severity,
            confidence=0.8 if severity != Severity.LOW else 0.7,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
