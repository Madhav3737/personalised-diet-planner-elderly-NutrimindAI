from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    ProfileCreate, ProfileResponse, MedicalHistoryCreate, MedicalHistoryResponse,
    AllergyResponse, PreferenceResponse
)
from app.services.auth_service import get_current_user
from app.services.profile_service import ProfileService

router = APIRouter()

@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_444_NOT_FOUND,
            detail="Profile not found. Please complete profile wizard."
        )
    # Fix: 444 is not a standard status, let's use 404
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete profile wizard."
        )
    return profile

@router.post("/me", response_model=ProfileResponse)
async def create_or_update_profile(
    profile_in: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    return await profile_service.create_or_update_profile(current_user.id, profile_in)

@router.get("/medical-history", response_model=MedicalHistoryResponse)
async def get_medical_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    med = await profile_service.get_medical_history(current_user.id)
    if not med:
        # Return empty/default medical history
        return MedicalHistoryResponse(
            id=0, user_id=current_user.id, diabetes=False, hypertension=False,
            heart_disease=False, kidney_disease=False, liver_disease=False,
            thyroid=False, cholesterol=False, arthritis=False, osteoporosis=False,
            digestive_disorders=False, others=""
        )
    return med

@router.post("/medical-history", response_model=MedicalHistoryResponse)
async def create_or_update_medical_history(
    med_in: MedicalHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    return await profile_service.create_or_update_medical_history(current_user.id, med_in)

@router.get("/allergies", response_model=List[AllergyResponse])
async def get_allergies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    return await profile_service.get_allergies(current_user.id)

@router.post("/allergies", response_model=List[AllergyResponse])
async def update_allergies(
    allergies: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    return await profile_service.update_allergies(current_user.id, allergies)

@router.get("/preferences", response_model=List[PreferenceResponse])
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    return await profile_service.get_preferences(current_user.id)

@router.post("/preferences", response_model=List[PreferenceResponse])
async def update_preferences(
    likes: List[str],
    dislikes: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_service = ProfileService(db)
    return await profile_service.update_preferences(current_user.id, likes, dislikes)
