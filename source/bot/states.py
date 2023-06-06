list_of_states = [
    "MENU",
    # Menu
    "TRACK_PRODUCT_CONV",
    "EDIT_TRACK_PRODUCTS_CONV",
    "ASKS",
    # User actions
    "DELETE_MYSELF",
    # Actions for products
    "TRACK",
    "PRODUCT_LIST",
    # Actions for notifications
    "ASK_ACTIONS",
    "APPLY_ASK",
    "REFUSE_ASK",
    # Commands
    "ADD_USER",
    "CANCEL_ADD_USER",
    "DOWNLOAD_DB",
    # Actions for special product
    "REMOVE",
    # Common actions
    "BACK",
]

STATES = {key: value for value, key in enumerate(list_of_states)}
