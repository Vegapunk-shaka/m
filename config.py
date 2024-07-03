import os


class Config(object):
    API_HASH = "03f1c29714a7ce9ed1819318427ea281"
    BOT_TOKEN = "6487314038:AAHyEnNRnf_imx_TmwaejYtu4rUIydayuEI"
    TELEGRAM_API = "20524455"
    OWNER = "1908235162"
    OWNER_USERNAME = "@ungaa_bungaa"
    PASSWORD = "lolicon"
    DATABASE_URL = "mongodb+srv://sanjitha:sanjitha01@cluster0.psghgex.mongodb.net/?retryWrites=true&w=majority"
    LOGCHANNEL = "-1001802445568"   # Add channel id as: "-100 + Actual_ID"
#USER_SESSION_STRING = "" # Premium account session string to upload upto 4GB (requires "LOGCHANNEL")

# tired of redeploying :(
#UPSTREAM_REPO = "https://github.com/yashoswalyo/MERGE-BOT"
#UPSTREAM_BRANCH = "master"
    GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID","root")
    USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", None)
    IS_PREMIUM = False
    MODES = ["video-video", "video-audio", "video-subtitle","extract-streams"]
