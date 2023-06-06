from typing import Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from source.bot.session_tokens.services import (
    add_token_for_user,
    check_token_in_db,
    remove_token_for_user,
)
from source.bot.users.queries import select_users
from source.database.admin import ProductAdmin, SessionTokenAdmin, UserAdmin
from source.settings import ADMIN_PASSWORD


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """Login the user and validate it"""

        form = await request.form()
        username, password = form["username"], form["password"]

        admin_users = await select_users(username=username, is_admin=True)

        if admin_users:
            user = admin_users[0]

            user_json = {
                k: v for k, v in user.__dict__.items() if k != "_sa_instance_state"
            }

            if username == user.username and password == ADMIN_PASSWORD:
                token = str(uuid4())
                await add_token_for_user(token=token, username=username)
                session_data = {
                    "user": user_json,
                    "token": token,
                }
                request.session.update(session_data)
                return True
        return False

    async def logout(self, request: Request) -> bool:
        """Clear the session"""

        token = request.session.get("token")
        await remove_token_for_user(token)
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        """Authenticates the user if he has a token"""

        token = request.session.get("token")
        token_exist = await check_token_in_db(token)

        if not token or not token_exist:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)


def get_admin_panel(web_app: FastAPI, engine: AsyncEngine) -> None:
    authentication_backend = AdminAuth(secret_key="secret_key")

    admin = Admin(
        app=web_app,
        title="Price Tracker Admin",
        engine=engine,
        authentication_backend=authentication_backend,
    )

    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(SessionTokenAdmin)
