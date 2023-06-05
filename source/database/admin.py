from sqladmin import ModelView
from source.database.models import User, Product, SessionToken


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

    # Form lines
    form_columns = [
        User.username,
        User.chat_id,
        User.is_admin,
    ]

    # Options
    column_sortable_list = [User.username, User.is_admin]
    column_searchable_list = [User.username, User.chat_id]

    # Permissions
    can_create = True
    can_edit = False
    can_delete = True
    can_view_details = True


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

    # Permissions
    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True


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
    # Export options
    can_export = False

    # Permissions
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
