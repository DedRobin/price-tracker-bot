from telegram.ext import ConversationHandler

ADMIN_ACTIONS, DATABASE, USERS, BACK, STOP = range(5)
CREATE_ADMIN, CHECK_ADMIN_KEY = range(5, 7)
USER_ACTIONS, REMOVE_USER = range(7, 9)
DB_ACTIONS, DOWNLOAD_DB_ACTIONS, DOWNLOAD_DB, UPLOAD_DB = range(9, 13)

END = ConversationHandler.END
TIMEOUT = ConversationHandler.TIMEOUT
