from typing import Annotated
from beanie import PydanticObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm

from backend.database.models.users import User, UserAPI, UserIn, UserRelation
from backend.database.service import relation_service, user_service
from backend.routers.auth import authenticate_user, get_current_user, get_user_by_name, login
from backend.util.auth import ChangePasswordForm, ResetPasswordForm
import backend.util.errors as E

router = APIRouter(
    prefix = "/users",
    tags = ["users"]
)

me_router = APIRouter(
    prefix = "/me"
)

ApiUser = Annotated[User, Depends(get_current_user)]

@me_router.get("/")
def get_this_user(user: ApiUser) -> UserAPI:
    return UserAPI(**user.dict())

@me_router.delete("/")
async def delete_user(user: ApiUser, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    await authenticate_user(form_data.username, form_data.password)
    success = await user_service.archive(user)
    if success:
        message = "User was archived! Will be deleted in 14 days!"
    else:
        message = "User could not be archived!"

    return { "message": message }

@me_router.put("/")
async def update_user(user: ApiUser, change_set: Annotated[dict, Body()]):
    try:
        new_info = await user_service.update_info(user, change_set)
    except E.InvalidUpdateOption as e:
        raise HTTPException(400, f"{e.option} is not a valid update option!")
    except:
        raise HTTPException(400, "Request encountered an error!")

    return {
        "message": "User data changed successfully!",
        "new_user_info": new_info
    }

@me_router.put("/change_password")
async def change_user_password(user: ApiUser, form_data: Annotated[ChangePasswordForm, Depends()]):
    print(form_data)
    try:
        await user_service.change_password(user, form_data)
    except:
        raise HTTPException(400, "Something went wrong!")

    print("Pw changed!")

@me_router.post("/friend/{user_id}")
async def add_as_friend(user: ApiUser, user_id: PydanticObjectId):
    u = await user_service.get_by_id(user_id)
    if not u:
        raise HTTPException(404, "User does not exist!")

    return {"message": "Friend request sent!", "username": u.username}

router.include_router(me_router)


@router.post("/")
async def create_user(user_info: UserIn):
    # TODO: This should probably be protected with an API key.
    try:
        u_id = await user_service.create_user(user_info)
    except:
        raise HTTPException(400, "User with name exists!")

    return { "id": u_id }

@router.get("/reset_password/{username}")
async def request_reset_password(username: str):
    try:
        await user_service.request_reset_password(username)
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.UserHasPendingRequest:
        raise HTTPException(400, "User has pending request!")

    return { "message": f"A request has been sent to the user's email address!" }

@router.put("/reset_password/{token}")
async def reset_password(token: str, passwords: ResetPasswordForm):
    try:
        await user_service.execute_password_reset(token, passwords)
    except E.TokenInvalid:
        raise HTTPException(401, "Token outdated or invalid!")
    except E.UserDoesNotExist:
        raise HTTPException(404, "User does not exist!")
    except E.UserNewPasswordDoesNotMatch:
        raise HTTPException(401, "Passwords don't match!")

    return { "message": "Password reset successfully!" }

@router.put("/reactivate")
async def unarchive_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    session_token_dict = await login(form_data)

    user = await get_user_by_name(form_data.username)
    if not user:
        raise HTTPException(404, "User does not exist!")

    success = await user_service.unarchive(user)
    if not success:
        raise HTTPException(400, "User is not archived!")

    return session_token_dict

@router.get("/{username}")
async def get_user_info(searching_user: ApiUser, username: str):
    u = await user_service.get_by_username(username)
    if not u:
        raise HTTPException(404, "User not found!")

    return UserAPI(**u.dict())

@router.post("/report/{user_id}")
def report_user(reporting_user: ApiUser, user_id: int):
    return {"message": "User reported successfully!", "user_id": user_id}

