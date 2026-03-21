from pathlib import Path

from papermentor_os.skills.loader import SkillLoader


def test_skill_loader_resolves_worker_bundle_from_filesystem() -> None:
    skill_root = Path(__file__).resolve().parents[2] / "skills"
    loader = SkillLoader(skill_root)

    bundle = loader.resolve_worker_skills(
        "LogicChainAgent",
        discipline="computer_science",
        stage="draft",
    )

    assert bundle.rubric_skills[0].metadata.versioned_id == "logic-chain-rubric@0.1.0"
    assert len(bundle.policy_skills) == 3
    assert len(bundle.output_schema_skills) == 3
    assert bundle.domain_skills[0].metadata.id == "computer-science-thesis-rules"


def test_skill_loader_resolves_literature_worker_rubric() -> None:
    skill_root = Path(__file__).resolve().parents[2] / "skills"
    loader = SkillLoader(skill_root)

    bundle = loader.resolve_worker_skills(
        "LiteratureSupportAgent",
        discipline="computer_science",
        stage="draft",
    )

    assert bundle.rubric_skills[0].metadata.versioned_id == "literature-support-rubric@0.1.0"


def test_skill_loader_resolves_novelty_worker_rubric() -> None:
    skill_root = Path(__file__).resolve().parents[2] / "skills"
    loader = SkillLoader(skill_root)

    bundle = loader.resolve_worker_skills(
        "NoveltyDepthAgent",
        discipline="computer_science",
        stage="draft",
    )

    assert bundle.rubric_skills[0].metadata.versioned_id == "novelty-depth-rubric@0.1.0"


def test_skill_loader_can_load_debate_rubric_directly() -> None:
    skill_root = Path(__file__).resolve().parents[2] / "skills"
    loader = SkillLoader(skill_root)

    skill = loader.load_skill("severity-resolution-rubric")

    assert skill.metadata.versioned_id == "severity-resolution-rubric@0.1.0"
