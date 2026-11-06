"""Structured profile extraction and human review schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EvidenceFact(BaseModel):
    value: str = Field(description="One factual claim stated in the resume")
    evidence: str = Field(description="Exact short quote copied from the resume text")


class ResumeExtraction(BaseModel):
    full_name: EvidenceFact | None
    email: EvidenceFact | None
    phone: EvidenceFact | None
    location: EvidenceFact | None
    professional_summary: EvidenceFact | None
    skills: list[EvidenceFact]
    education: list[EvidenceFact]
    work_experience: list[EvidenceFact]
    projects: list[EvidenceFact]
    certifications: list[EvidenceFact]


class ProfileReview(BaseModel):
    """User-edited profile values, confirmed by the authenticated owner."""

    full_name: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=200)
    professional_summary: str | None = Field(default=None, max_length=4000)
    skills: list[str] = Field(default_factory=list, max_length=200)
    education: list[str] = Field(default_factory=list, max_length=100)
    work_experience: list[str] = Field(default_factory=list, max_length=100)
    projects: list[str] = Field(default_factory=list, max_length=100)
    certifications: list[str] = Field(default_factory=list, max_length=100)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: dict
    confirmed: bool
    source_filename: str | None
