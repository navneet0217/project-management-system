from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import auth_rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.user import LoginRequest, RefreshRequest, TokenPair, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair, dependencies=[Depends(auth_rate_limit)])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, data.email, data.password)
    return auth_service.issue_tokens(db, user)


@router.post("/refresh", response_model=TokenPair, dependencies=[Depends(auth_rate_limit)])
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.rotate_refresh_token(db, data.refresh_token)


@router.post("/logout", status_code=204)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.revoke_refresh_token(db, data.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
