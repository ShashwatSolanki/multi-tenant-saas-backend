from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserLogin
from app.core.security import verify_password, create_access_token

from app.core.security import hash_password
from app.schemas.user import UserCreate, UserResponse
from app.models.organization import Organization

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.email == user_data.email,
            User.organization_id == user_data.organization_id
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "user_id": str(user.id),
        "organization_id": str(user.organization_id),
    }

    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):

    # Check if organization exists
    org = db.query(Organization).filter(
        Organization.id == user_data.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=400, detail="Organization not found")

    # Check duplicate email inside tenant
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.organization_id == user_data.organization_id
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists in this organization")

    # Hash password
    hashed_password = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        organization_id=user_data.organization_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user