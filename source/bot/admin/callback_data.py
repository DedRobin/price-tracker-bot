from telegram.ext import ConversationHandler

ADMIN_ACTIONS, DATABASE, STOP = range(3)
CREATE_ADMIN, CHECK_ADMIN_KEY, GO_BACK = range(3, 6)
DB_ACTIONS, DOWNLOAD_DB_ACTIONS, DOWNLOAD_DB, UPLOAD_DB = range(6, 10)

END = ConversationHandler.END
