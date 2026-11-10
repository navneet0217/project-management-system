from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import auth_rate_limit
from app.db.session import get_db
from app.models import Role, User
from app.schemas.user import (
    EmailRequest,
    LoginRequest,
    MessageOut,
    RefreshRequest,
    SignupRequest,
    TokenPair,
    TokenRequest,
    UserCreate,
    UserOut,
)
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=MessageOut, status_code=201, dependencies=[Depends(auth_rate_limit)])
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Role is forced to DEVELOPER; the account cannot log in until the emailed link is used.
    user = user_service.create_user(
        db,
        UserCreate(email=data.email, full_name=data.full_name, password=data.password, role=Role.DEVELOPER),
        verified=False,
    )
    auth_service.send_verification(db, user)
    return MessageOut(detail="Account created. Check your email for the verification link.")


@router.post("/verify-email", response_model=MessageOut, dependencies=[Depends(auth_rate_limit)])
def verify_email(data: TokenRequest, db: Session = Depends(get_db)):
    auth_service.verify_email(db, data.token)
    return MessageOut(detail="Email verified. You can sign in now.")


@router.post("/resend-verification", response_model=MessageOut, status_code=202, dependencies=[Depends(auth_rate_limit)])
def resend_verification(data: EmailRequest, db: Session = Depends(get_db)):
    auth_service.resend_verification(db, data.email)
    return MessageOut(detail="If that account needs verification, a new link is on its way.")


# Forgot/reset password is switched off for now (re-enable later; service functions and tests are kept).
# @router.post("/forgot-password", response_model=MessageOut, status_code=202, dependencies=[Depends(auth_rate_limit)])
# def forgot_password(data: EmailRequest, db: Session = Depends(get_db)):
#     auth_service.forgot_password(db, data.email)
#     return MessageOut(detail="If that email is registered, a reset link is on its way.")
#
#
# @router.post("/reset-password", response_model=MessageOut, dependencies=[Depends(auth_rate_limit)])
# def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
#     auth_service.reset_password(db, data.token, data.password)
#     return MessageOut(detail="Password updated. Please sign in with your new password.")


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
