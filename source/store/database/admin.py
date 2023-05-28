from sqladmin import ModelView
from source.store.database.models import User, Product
from sqladmin.authentication import AuthenticationBackend
from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from typing import Optional

from uuid import uuid4


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """Login the user and validate him/her"""

        form = await request.form()
        username, password = form["username"], form["password"]

        # Validate
        token = uuid4()
        request.session.update({"token": str(token)})

        return True

    async def logout(self, request: Request) -> bool:
        """Clear the session"""

        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        token = request.session.get("token")

        if not token:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        # Check the token in depth


class UserAdmin(ModelView, model=User):
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.username,
        User.chat_id,
        User.is_admin,
    ]


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.product_link,
        Product.current_price,
        Product.previous_price,
        Product.updated_at,
    ]
