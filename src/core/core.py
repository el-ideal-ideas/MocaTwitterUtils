# -- Imports --------------------------------------------------------------------------

from pathlib import Path
from .. import moca_modules as mzk

# -------------------------------------------------------------------------- Imports --

# -- Variables --------------------------------------------------------------------------

# version
VERSION: str = mzk.get_str_from_file(Path(__file__).parent.joinpath('.version'))

# path
TOP_DIR: Path = Path(__file__).parent.parent.parent
CONFIG_DIR: Path = TOP_DIR.joinpath('configs')
LOG_DIR: Path = TOP_DIR.joinpath('logs')
SRC_DIR: Path = TOP_DIR.joinpath('src')
STORAGE_DIR: Path = TOP_DIR.joinpath('storage')

# create directories if not exists.
for __dir in [CONFIG_DIR, LOG_DIR, STORAGE_DIR]:
    __dir.mkdir(parents=True, exist_ok=True)
del __dir

# configs
SYSTEM_CONFIG: Path = CONFIG_DIR.joinpath('system.json')
SERVER_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('server.json'))
SANIC_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('sanic.json'))
TWITTER_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('twitter.json'))
DB_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('database.json'))
IP_BLACKLIST_FILE: Path = CONFIG_DIR.joinpath('ip_blacklist.json')
API_KEY_FILE: Path = CONFIG_DIR.joinpath('api_key.json')
system_config: mzk.MocaConfig = mzk.MocaConfig(SYSTEM_CONFIG, manual_reload=True)
ip_blacklist: mzk.MocaSynchronizedJSONListFile = mzk.MocaSynchronizedJSONListFile(
    IP_BLACKLIST_FILE, manual_reload=True, remove_duplicates=True,
)
api_key_config: mzk.MocaSynchronizedJSONListFile = mzk.MocaSynchronizedJSONListFile(
    API_KEY_FILE, manual_reload=True
)
moca_twitter: mzk.MocaTwitter = mzk.MocaTwitter(
    TWITTER_CONFIG['CONSUMER_KEY'],
    TWITTER_CONFIG['CONSUMER_SECRET'],
    TWITTER_CONFIG['ACCESS_TOKEN'],
    TWITTER_CONFIG['ACCESS_TOKEN_SECRET']
)

INSERT_TWEET_QUERY = mzk.get_str_from_file(Path(__file__).parent.joinpath('insert_tweet.sql')).replace(
    '[el]#moca_prefix#', DB_CONFIG['mysql']['prefix']
)
ADD_USER_QUERY = mzk.get_str_from_file(Path(__file__).parent.joinpath('add_user.sql')).replace(
    '[el]#moca_prefix#', DB_CONFIG['mysql']['prefix']
)
UPDATE_USER_QUERY = mzk.get_str_from_file(Path(__file__).parent.joinpath('update_user.sql')).replace(
    '[el]#moca_prefix#', DB_CONFIG['mysql']['prefix']
)
GET_TWEETS_QUERY = mzk.get_str_from_file(Path(__file__).parent.joinpath('get_tweets.sql')).replace(
    '[el]#moca_prefix#', DB_CONFIG['mysql']['prefix']
)
COUNT_TWEETS_QUERY = mzk.get_str_from_file(Path(__file__).parent.joinpath('count_tweets.sql')).replace(
    '[el]#moca_prefix#', DB_CONFIG['mysql']['prefix']
)
SCREEN_NAME_TO_ID_QUERY = mzk.get_str_from_file(Path(__file__).parent.joinpath('screen_name_to_id.sql')).replace(
    '[el]#moca_prefix#', DB_CONFIG['mysql']['prefix']
)

# -------------------------------------------------------------------------- Variables --
