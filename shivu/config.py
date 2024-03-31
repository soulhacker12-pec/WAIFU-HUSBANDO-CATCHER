class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "6783092268"
    sudo_users = "6783092268"
    GROUP_ID = -1002073720399
    TOKEN = "6802425596:AAEN6NJCn_1y49lOLf8l07vfpjVQXtbIAo0"
    mongo_url = "mongodb+srv://zhuofan21001:9Bpb5voEiKYcnUQm@cluster0.mibzqh9.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://te.legra.ph/file/0d1c4aa40dcdce4552084.jpg", "https://telegra.ph/file/4211fb191383d895dab9d.jpg"]
    SUPPORT_CHAT = "PokemonUniteGC"
    UPDATE_CHAT = "PokemonUniteGC"
    BOT_USERNAME = "graBxWaifuRobot"
    CHARA_CHANNEL_ID = "-1002111937813"
    api_id = 28213805
    api_hash = "8f80142dfef1a696bee7f6ab4f6ece34"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
