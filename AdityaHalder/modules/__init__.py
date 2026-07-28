import sys
from .. import console

def check_variables():
    if console.API_ID == 0:
        console.logs(__name__).info("❌ 'API_ID' - Not found❗")
        sys.exit()
    if not console.API_HASH:
        console.logs(__name__).info("❌ 'API_HASH' - Not found❗")
        sys.exit()
    if not console.BOT_TOKEN:
        console.logs(__name__).info("❌ 'BOT_TOKEN' - Not found❗")
        sys.exit()
    if not any([console.STRING1, console.STRING2, console.STRING3, console.STRING4, console.STRING5]):
        console.logs(__name__).info("❌ 'STRING_SESSION' - Not found❗")
        sys.exit()
    if not console.DATABASE_URL or not console.DATABASE_PASSWORD:
        console.logs(__name__).info("❌ 'DATABASE_URL' or 'DATABASE_PASSWORD' - Not found❗")
        sys.exit()
    if console.OWNER_ID == 0:
        console.logs(__name__).info("❌ 'OWNER_ID' - Not found❗")
        sys.exit()
    if console.LOG_GROUP_ID == 0:
        console.logs(__name__).info("❌ 'LOG_GROUP_ID' - Not found❗")
        sys.exit()

check_variables()
