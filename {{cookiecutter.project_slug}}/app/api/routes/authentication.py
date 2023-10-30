"""Authentication."""
import base64
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse, Response

from app.api.database.models.auth import BasicAuth, basic_auth
from app.api.database.models.token import Token
from app.api.database.models.user import UserSchema
from app.api.services import authentication_service
from app.core.constant import ACCESS_TOKEN_EXPIRE_MINUTES

# to get a string like this run:
# openssl rand -hex 32

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login token."""
    user = authentication_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = authentication_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/logout")
async def route_logout_and_remove_cookie():
    """Logout and remove cookie."""
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization")
    return response


@router.get("/login")
async def login_basic(auth: BasicAuth = Depends(basic_auth)):
    """Login and get token."""
    if not auth:
        return Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)

    try:
        decoded = base64.b64decode(auth).decode("ascii")
        username, _, password = decoded.partition(":")
        user = authentication_service.authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = authentication_service.create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        token = jsonable_encoder(access_token)

        response = RedirectResponse(url="/docs")
        response.set_cookie(
            "Authorization",
            value=f"Bearer {token}",
            httponly=True,
            max_age=1800,
            expires=1800,
        )
        return response

    except HTTPException:
        return Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)


@router.get("/docs")
# pylint: disable=unused-argument
async def get_documentation(current_user: UserSchema = Depends(authentication_service.get_current_active_user)):
    """Get documentation."""
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: UserSchema = Depends(authentication_service.get_current_active_user)):
    """Get information of current user."""
    return current_user
