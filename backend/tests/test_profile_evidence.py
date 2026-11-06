from job_agent.schemas.profile import EvidenceFact, ResumeExtraction
from job_agent.services.profile_extractor import keep_only_source_supported


def test_drops_claims_without_exact_source_evidence() -> None:
    extracted = ResumeExtraction(
        full_name=EvidenceFact(value="Jordan Example", evidence="Jordan Example"),
        email=None,
        phone=None,
        location=None,
        professional_summary=None,
        skills=[
            EvidenceFact(value="Python", evidence="Skills: Python"),
            EvidenceFact(value="Kubernetes", evidence="Kubernetes expert"),
        ],
        education=[],
        work_experience=[],
        projects=[],
        certifications=[],
    )

    cleaned, rejected = keep_only_source_supported(extracted, "Jordan Example\nSkills: Python")

    assert [fact.value for fact in cleaned.skills] == ["Python"]
    assert rejected == ["skills[1]"]
