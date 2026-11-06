"""Authentication and authenticated profile endpoints."""

from __future__ import annotations

import hashlib
import re
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from job_agent.core.config import get_settings
from job_agent.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from job_agent.db.session import get_db
from job_agent.models.profile import User, UserProfile
from job_agent.schemas.auth import RegisterRequest, TokenResponse, UserResponse
from job_agent.schemas.profile import ProfileResponse, ProfileReview
from job_agent.services.profile_extractor import ProfileExtractionError, ProfileExtractor
from job_agent.services.resume_parser import ResumeParseError, extract_resume_text

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> User:
    user = User(email=str(payload.email).casefold(), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    db.refresh(user)
    return user


@router.post("/auth/token", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == form.username.casefold()))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/profiles/me/resume", response_model=ProfileResponse)
async def parse_resume(
    file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfileResponse:
    settings = get_settings()
    filename = _safe_filename(file.filename or "resume")
    try:
        content = await file.read(settings.max_resume_bytes + 1)
        if len(content) > settings.max_resume_bytes:
            raise ResumeParseError("Resume exceeds the configured upload limit")
        resume_text = extract_resume_text(filename, content, settings.max_resume_bytes)
    except ResumeParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()

    try:
        extraction, rejected = await ProfileExtractor().extract(resume_text)
    except ProfileExtractionError as exc:
        code = 503 if "not configured" in str(exc) else 502
        raise HTTPException(status_code=code, detail=str(exc)) from exc

    profile_data = extraction.model_dump(mode="json")
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.data = profile_data
    profile.confirmed = False
    profile.source_filename = filename
    profile.source_sha256 = hashlib.sha256(content).hexdigest()
    db.commit()
    db.refresh(profile)
    return ProfileResponse(
        data={**profile.data, "unsupported_claims_discarded": rejected},
        confirmed=False,
        source_filename=profile.source_filename,
    )


@router.get("/profiles/me", response_model=ProfileResponse)
def get_profile(
    user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]
) -> ProfileResponse:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile exists yet")
    return ProfileResponse(
        data=profile.data, confirmed=profile.confirmed, source_filename=profile.source_filename
    )


@router.put("/profiles/me", response_model=ProfileResponse)
def confirm_profile(
    payload: ProfileReview,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfileResponse:
    """Replace the draft with user-reviewed facts and mark it confirmed."""

    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.data = payload.model_dump(mode="json")
    profile.confirmed = True
    db.commit()
    db.refresh(profile)
    return ProfileResponse(
        data=profile.data, confirmed=True, source_filename=profile.source_filename
    )


def _safe_filename(filename: str) -> str:
    basename = filename.replace("\\", "/").split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", basename).strip(" .")[:255]
    if not cleaned or "." not in cleaned:
        raise HTTPException(status_code=422, detail="A PDF or DOCX filename is required")
    return cleaned
