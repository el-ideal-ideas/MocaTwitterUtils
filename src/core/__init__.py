# -- Imports --------------------------------------------------------------------------

from pathlib import Path
from warnings import catch_warnings, simplefilter
from .core import (
    VERSION, TOP_DIR, CONFIG_DIR, LOG_DIR, SRC_DIR, STORAGE_DIR, SYSTEM_CONFIG, SANIC_CONFIG, SERVER_CONFIG,
    IP_BLACKLIST_FILE, API_KEY_FILE, system_config, ip_blacklist, TWITTER_CONFIG, moca_twitter, DB_CONFIG,
    INSERT_TWEET_QUERY, ADD_USER_QUERY, UPDATE_USER_QUERY, GET_TWEETS_QUERY, COUNT_TWEETS_QUERY,
    SCREEN_NAME_TO_ID_QUERY
)
from .db import redis, mysql, cursor
from .. import moca_modules as mzk

# -------------------------------------------------------------------------- Imports --

# -- Init --------------------------------------------------------------------------

__users_table = mzk.get_str_from_file(Path(__file__).parent.joinpath('users_table.sql'))
__tweets_table = mzk.get_str_from_file(Path(__file__).parent.joinpath('tweets_table.sql'))
with catch_warnings():
    simplefilter("ignore")
    cursor.execute(__users_table % (DB_CONFIG['mysql']['prefix'],))
    mysql.commit()
    cursor.execute(__tweets_table % (DB_CONFIG['mysql']['prefix'], DB_CONFIG['mysql']['prefix']))
    mysql.commit()
del __users_table, __tweets_table

# -------------------------------------------------------------------------- Init --
