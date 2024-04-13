class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = 6783092268
    sudo_users = "5162659136",5162659136,"6447641540","1782205703",1782205703,"1470441905","5746762799","6616253205","6783092268","2016154439","1861645831","666686141","6666861412",6666861412,6999153738,6616253205
    GROUP_ID = -1002073720399
    TOKEN = "7135340603:AAFwlaTTB2cB9xU1f_LhUYoRObhqy1cUdjw"
    mongo_url = "mongodb+srv://zhuofan21001:9Bpb5voEiKYcnUQm@cluster0.mibzqh9.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://te.legra.ph/file/9f81d51fcc0cf0284a99f.jpg","https://te.legra.ph/file/9f81d51fcc0cf0284a99f.jpg"]
    SUPPORT_CHAT = "PokemonUniteGC"
    UPDATE_CHAT = "chuTiyaSupport"
    BOT_USERNAME = "graBxWaifuRobot"
    CHARA_CHANNEL_ID = "-1002111937813"
    api_id = 28213805
    api_hash = "8f80142dfef1a696bee7f6ab4f6ece34"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
