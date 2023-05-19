list_of_states = [
    "MENU",
    # Menu
    "TRACK_PRODUCT_CONV",
    "EDIT_TRACK_PRODUCTS_CONV",
    # Actions for
    "TRACK",
    "PRODUCT_LIST",
    # Commands
    "ADD_USER",
    "CANCEL_ADD_USER",
    "DOWNLOAD_DB",
    # Actions for special product
    "REMOVE",
    # Common actions
    "BACK"
]

STATES = {key: value for value, key in enumerate(list_of_states)}
