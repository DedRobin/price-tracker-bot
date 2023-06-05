import base64
import binascii
import hashlib
import os

from sqladmin import ModelView
from source.database.models import User, Product, SessionToken
from sqladmin.authentication import AuthenticationBackend
from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from typing import Optional

from uuid import uuid4
from source.database.queries import select_users
from source.webserver.services import add_token_for_user, check_token_in_db

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


class AdminAuth(AuthenticationBackend):

    async def login(self, request: Request) -> bool:
        """Login the user and validate it"""

        form = await request.form()
        username, password = form["username"], form["password"]

        admins = await select_users(is_admin=True)
        admin_usernames = [admin.username for admin in admins]

        password = password.encode("utf8")
        admin_password = ADMIN_PASSWORD.encode("utf8")
        hash_password = hashlib.md5(password).hexdigest()
        hash_admin_password = hashlib.md5(admin_password).hexdigest()

        # Conditions
        user_is_admin = username in admin_usernames
        passwords_match = hash_password == hash_admin_password

        if passwords_match and user_is_admin:
            token = str(uuid4())
            await add_token_for_user(token=token, username=username)
            request.session.update({"token": token})
            return True

        return False

    async def logout(self, request: Request) -> bool:
        """Clear the session"""

        # Delete token

        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        """Authenticates the user if he has a token"""

        token = request.session.get("token")
        token_exist = await check_token_in_db(token)

        if not token or not token_exist:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)


class UserAdmin(ModelView, model=User):
    # Metadata
    icon = "fa-solid fa-user"

    # Columns
    column_list = [
        User.id,
        User.username,
        User.chat_id,
        User.is_admin,
    ]

    # Options
    column_sortable_list = [User.username, User.is_admin]
    column_searchable_list = [User.username, User.chat_id]


class ProductAdmin(ModelView, model=Product):
    # Columns
    column_list = [
        Product.id,
        Product.name,
        Product.product_link,
        Product.current_price,
        Product.previous_price,
        Product.updated_at,
    ]

    # Options
    column_sortable_list = [
        Product.product_link,
        Product.name,
        Product.current_price,
        Product.previous_price,
        Product.updated_at,
    ]


class SessionTokenAdmin(ModelView, model=SessionToken):
    # Columns
    column_list = [
        SessionToken.id,
        SessionToken.token,
        SessionToken.user_id,
    ]

    # Options
    column_sortable_list = [
        SessionToken.id,
        SessionToken.token,
        SessionToken.user_id,
    ]
