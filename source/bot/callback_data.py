list_of_states = [
    # Startpoint
    "MENU",

    # Menu
    "TRACK_PRODUCT_CONV",
    "EDIT_TRACK_PRODUCTS_CONV",
    "ASKS",

    # Actions for products
    "TRACK",
    "PRODUCT_LIST",

    # Actions for notifications
    "ASK_ACTIONS",
    "APPLY_ASK",
    "REFUSE_ASK",

    # Admin commands
    "ADMIN_MENU",
    "CREATE_ADMIN",
    "NO_CREATE_ADMIN",
    "DOWNLOAD_DB",

    # Actions for special product
    "REMOVE",

    # Common actions
    "BACK",
]

STATES = {key: value for value, key in enumerate(list_of_states)}
STOP = 100
