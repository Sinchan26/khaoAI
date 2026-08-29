from fastapi import APIRouter, HTTPException, status, Depends
from ..models.auth import UserRegister, UserLogin, TokenResponse, UserProfile
from ..services.auth_service import auth_service
from ..middleware.auth_middleware import require_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister):
    try:
        return auth_service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    try:
        return auth_service.login(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me", response_model=UserProfile)
def get_current_user_profile(user: UserProfile = Depends(require_current_user)):
    return user
