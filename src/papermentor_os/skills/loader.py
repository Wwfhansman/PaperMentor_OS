from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from papermentor_os.skills.models import SkillDocument, SkillMetadata


GLOBAL_POLICY_SKILLS = [
    "no-ghostwriting-policy",
    "education-guidance-policy",
    "evidence-required-policy",
]

GLOBAL_OUTPUT_SCHEMA_SKILLS = [
    "review-finding-schema",
    "dimension-report-schema",
    "final-report-schema",
]

DEFAULT_DOMAIN_SKILLS = [
    "computer-science-thesis-rules",
]

WORKER_RUBRIC_SKILLS = {
    "TopicScopeAgent": "topic-clarity-rubric",
    "LogicChainAgent": "logic-chain-rubric",
    "LiteratureSupportAgent": "literature-support-rubric",
    "NoveltyDepthAgent": "novelty-depth-rubric",
    "WritingFormatAgent": "writing-format-rubric",
}

BODY_CANDIDATE_FILES = [
    "prompt.md",
    "rubric.md",
    "policy.md",
    "rules.md",
    "schema.json",
    "output_schema.json",
]


@dataclass(slots=True)
class SkillBundle:
    rubric_skills: list[SkillDocument]
    policy_skills: list[SkillDocument]
    output_schema_skills: list[SkillDocument]
    domain_skills: list[SkillDocument]

    def primary_rubric_version(self, fallback: str) -> str:
        if self.rubric_skills:
            return self.rubric_skills[0].metadata.versioned_id
        return fallback


class SkillLoader:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)

    def load_skill(self, skill_id: str, version: str | None = None) -> SkillDocument:
        skill_dir = self.root_dir / skill_id
        if not skill_dir.exists():
            raise FileNotFoundError(f"Skill '{skill_id}' not found in {self.root_dir}.")

        metadata_path = skill_dir / "skill.yaml"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Skill '{skill_id}' is missing skill.yaml.")

        raw_metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        metadata = SkillMetadata.model_validate(raw_metadata)
        if version is not None and metadata.version != version:
            raise ValueError(
                f"Skill '{skill_id}' version mismatch: expected {version}, got {metadata.version}."
            )

        body_path = self._find_body_path(skill_dir)
        body = body_path.read_text(encoding="utf-8") if body_path is not None else ""
        return SkillDocument(
            metadata=metadata,
            body=body,
            body_path=str(body_path) if body_path is not None else None,
        )

    def resolve_worker_skills(
        self,
        worker_id: str,
        *,
        discipline: str,
        stage: str,
    ) -> SkillBundle:
        rubric_skill_id = WORKER_RUBRIC_SKILLS.get(worker_id)
        if rubric_skill_id is None:
            raise KeyError(f"No rubric skill mapping configured for worker '{worker_id}'.")

        rubric_skill = self.load_skill(rubric_skill_id)
        self._validate_context(rubric_skill, discipline=discipline, stage=stage)

        policy_skills = [self.load_skill(skill_id) for skill_id in GLOBAL_POLICY_SKILLS]
        output_schema_skills = [self.load_skill(skill_id) for skill_id in GLOBAL_OUTPUT_SCHEMA_SKILLS]
        domain_skills = [
            skill
            for skill in (self.load_skill(skill_id) for skill_id in DEFAULT_DOMAIN_SKILLS)
            if self._skill_matches_context(skill, discipline=discipline, stage=stage)
        ]

        return SkillBundle(
            rubric_skills=[rubric_skill],
            policy_skills=policy_skills,
            output_schema_skills=output_schema_skills,
            domain_skills=domain_skills,
        )

    def _validate_context(self, skill: SkillDocument, *, discipline: str, stage: str) -> None:
        if not self._skill_matches_context(skill, discipline=discipline, stage=stage):
            raise ValueError(
                f"Skill '{skill.metadata.id}' does not match discipline={discipline}, stage={stage}."
            )

    def _skill_matches_context(self, skill: SkillDocument, *, discipline: str, stage: str) -> bool:
        discipline_ok = (
            not skill.metadata.applicable_disciplines
            or discipline in skill.metadata.applicable_disciplines
        )
        stage_ok = not skill.metadata.applicable_stages or stage in skill.metadata.applicable_stages
        return discipline_ok and stage_ok and skill.metadata.status == "active"

    def _find_body_path(self, skill_dir: Path) -> Path | None:
        for candidate in BODY_CANDIDATE_FILES:
            candidate_path = skill_dir / candidate
            if candidate_path.exists():
                return candidate_path
        return None
