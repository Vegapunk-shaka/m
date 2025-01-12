import os


class Config(object):
    API_HASH = "edefebe693e029e6aca6c7c1df2745ec"
    BOT_TOKEN = "7296554134:AAHlDveis7GXhbNcUlQ0I1ndFIIdorI-4LY"
    TELEGRAM_API = "18530329"
    OWNER = "1908235162"
    OWNER_USERNAME = "@ungaa_bungaa"
    PASSWORD = "lolicon"
    DATABASE_URL = "mongodb+srv://sanjitha:sanjitha01@cluster0.psghgex.mongodb.net/?retryWrites=true&w=majority"
    LOGCHANNEL = "-1001930986503"   # Add channel id as: "-100 + Actual_ID"
#USER_SESSION_STRING = "" # Premium account session string to upload upto 4GB (requires "LOGCHANNEL")

# tired of redeploying :(
#UPSTREAM_REPO = "https://github.com/yashoswalyo/MERGE-BOT"
#UPSTREAM_BRANCH = "master"
    GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID","root")
    USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None)
    IS_PREMIUM = False
    MODES = ["video-video", "video-audio", "video-subtitle","extract-streams"]
