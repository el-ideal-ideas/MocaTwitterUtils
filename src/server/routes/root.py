# -- Imports --------------------------------------------------------------------------

from typing import (
    Tuple
)
from sanic import Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse, text, json as original_json, file
from orjson import dumps as orjson_dumps
from functools import partial
json = partial(original_json, dumps=orjson_dumps)
from sanic.exceptions import Forbidden, ServerError
from time import time
from pymysql import IntegrityError, MySQLError
from ... import moca_modules as mzk
from ... import core
from .utils import check_root_pass

# -------------------------------------------------------------------------- Imports --

# -- Private --------------------------------------------------------------------------

ONE_DAY = 86400  # 1 * 60 * 60 * 24


async def __add_user(request: Request, info: dict) -> None:
    try:
        await request.app.mysql.execute_aio(
            core.ADD_USER_QUERY,
            (
                info.get('id', 0), info.get('name', ''), info.get('screen_name', ''), info.get('location', ''),
                info.get('description', ''), info.get('url', ''), info.get('followers_count', 0),
                info.get('friends_count', 0),
                info.get('listed_count', 0), info.get('favourites_count', 0), info.get('profile_background_color', ''),
                info.get('profile_background_image_url', ''), info.get('profile_background_image_url_https', ''),
                info.get('profile_image_url', ''), info.get('profile_image_url_https', ''),
                info.get('profile_banner_url', ''),
                info.get('profile_link_color', ''), info.get('profile_sidebar_border_color', ''),
                info.get('profile_sidebar_fill_color', ''), info.get('profile_text_color', ''),
                info.get('created_at', '')
            ),
            True
        )
    except IntegrityError:
        await request.app.mysql.execute_aio(
            core.UPDATE_USER_QUERY,
            (
                info.get('name', ''), info.get('screen_name', ''), info.get('location', ''),
                info.get('description', ''), info.get('url', ''), info.get('followers_count', 0),
                info.get('friends_count', 0),
                info.get('listed_count', 0), info.get('favourites_count', 0), info.get('profile_background_color', ''),
                info.get('profile_background_image_url', ''), info.get('profile_background_image_url_https', ''),
                info.get('profile_image_url', ''), info.get('profile_image_url_https', ''),
                info.get('profile_banner_url', ''),
                info.get('profile_link_color', ''), info.get('profile_sidebar_border_color', ''),
                info.get('profile_sidebar_fill_color', ''), info.get('profile_text_color', ''), info.get('id', 0)
            ),
            True
        )


async def __get_info(request: Request, screen_name: str, force_refresh=False) -> dict:
    if not force_refresh:
        info, timestamp = request.app.simple_cache.get('twitter-info-' + screen_name, tuple, (None, None))
        if info is None or (time() - timestamp) > 86400:
            info = await request.app.redis.get('twitter-info-' + screen_name)
    else:
        info = None
    if info is None:
        info = request.app.twitter.get_user_info(screen_name)
        request.app.simple_cache.set('twitter-info-' + screen_name, (info, time()))
        await request.app.redis.set('twitter-info-' + screen_name, info, ONE_DAY)
        icon_url = info.get('profile_image_url_https', None)
        icon_ext = icon_url.split('.')[-1]
        if icon_url is not None:
            core.STORAGE_DIR.joinpath('icon').joinpath(info.get('screen_name', '_')).mkdir(parents=True, exist_ok=True)
            await mzk.aio_wget(
                icon_url,
                core.STORAGE_DIR.joinpath('icon').joinpath(info.get('screen_name', '_')).joinpath(f'normal.{icon_ext}')
            )
            await mzk.aio_wget(
                icon_url.replace('_normal', '_mini'),
                core.STORAGE_DIR.joinpath('icon').joinpath(info.get('screen_name', '_')).joinpath(f'mini.{icon_ext}')
            )
            await mzk.aio_wget(
                icon_url.replace('_normal', '_bigger'),
                core.STORAGE_DIR.joinpath('icon').joinpath(info.get('screen_name', '_')).joinpath(f'bigger.{icon_ext}')
            )
            await mzk.aio_wget(
                icon_url.replace('_normal', ''),
                core.STORAGE_DIR.joinpath('icon').joinpath(info.get('screen_name', '_')).joinpath(f'raw.{icon_ext}')
            )
        try:
            await __add_user(request, info)
        except MySQLError:
            request.app.simple_cache.set('twitter-info-' + screen_name, (None, None))
            await request.app.redis.delete('twitter-info-' + screen_name)
            raise ServerError("Can't save twitter info to database. Please contact to the administrator.")
    return info


async def __get_description(request: Request, screen_name: str) -> str:
    info = await __get_info(request, screen_name)
    return info.get('description', '')


async def __get_icon(request: Request, screen_name: str) -> dict:
    # Warning!!
    # This function will check the icon url per request.
    # If reach the rate limit, Maybe blocked by Twitter.
    info = await __get_info(request, screen_name)
    url = info.get('profile_image_url_https', '')
    status = mzk.wcheck(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4352.0 Safari/537.36'
        }
    )
    if not status:
        info = await __get_info(request, screen_name, force_refresh=True)
        url = info.get('profile_image_url_https', '')
    return {
        'normal': url,
        'mini': url.replace('_normal', '_mini'),
        'bigger': url.replace('_normal', '_bigger'),
        'raw': url.replace('_normal', '')
    }


async def __save_user_timeline(request: Request, screen_name: str) -> None:
    info = await __get_info(request, screen_name)
    user_id = info.get('id', 0)
    pool = await request.app.mysql.get_a_aio_pool()
    async with pool.acquire() as con:
        async with con.cursor() as cur:
            for tweet in request.app.twitter.get_timeline(
                    screen_name, count=200, exclude_replies=False, include_rts=True, include_entities=True
            ):
                data = tweet._json
                await cur.execute(
                    core.INSERT_TWEET_QUERY,
                    (data['id'],
                     user_id,
                     data['text'],
                     data['created_at'],
                     data['source'].split('>')[1].split('<')[0],
                     data['id'])
                )
        await con.commit()


# -------------------------------------------------------------------------- Private --

# -- Blueprint --------------------------------------------------------------------------

root: Blueprint = Blueprint('root', None)


@root.route('/get-user-info', {'GET', 'POST', 'OPTIONS'})
async def get_user_info(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    try:
        return json(await __get_info(request, screen_name))
    except mzk.TweepError:
        raise ServerError('Could not get info from Twitter.')


@root.route('/get-description', {'GET', 'POST', 'OPTIONS'})
async def get_description(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    try:
        return text(await __get_description(request, screen_name))
    except mzk.TweepError:
        raise ServerError('Could not get info from Twitter.')


@root.route('/get-icon', {'GET', 'POST', 'OPTIONS'})
async def get_icon(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    try:
        return json(await __get_icon(request, screen_name))
    except mzk.TweepError:
        raise ServerError('Could not get info from Twitter.')


@root.route('/get-normal-icon', {'GET', 'POST', 'OPTIONS'})
async def get_normal_icon(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    path = core.STORAGE_DIR.joinpath('icon').joinpath(screen_name)
    if not path.is_dir():
        await __get_info(request, screen_name, True)
    for icon in path.iterdir():
        if icon.name.startswith('normal'):
            return await file(str(icon), filename=f'{screen_name}-{icon.name}')


@root.route('/get-mini-icon', {'GET', 'POST', 'OPTIONS'})
async def get_mini_icon(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    path = core.STORAGE_DIR.joinpath('icon').joinpath(screen_name)
    if not path.is_dir():
        await __get_info(request, screen_name, True)
    for icon in path.iterdir():
        if icon.name.startswith('mini'):
            return await file(str(icon), filename=f'{screen_name}-{icon.name}')


@root.route('/get-bigger-icon', {'GET', 'POST', 'OPTIONS'})
async def get_bigger_icon(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    path = core.STORAGE_DIR.joinpath('icon').joinpath(screen_name)
    if not path.is_dir():
        await __get_info(request, screen_name, True)
    for icon in path.iterdir():
        if icon.name.startswith('bigger'):
            return await file(str(icon), filename=f'{screen_name}-{icon.name}')


@root.route('/get-raw-icon', {'GET', 'POST', 'OPTIONS'})
async def get_raw_icon(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    path = core.STORAGE_DIR.joinpath('icon').joinpath(screen_name)
    if not path.is_dir():
        await __get_info(request, screen_name, True)
    for icon in path.iterdir():
        if icon.name.startswith('raw'):
            return await file(str(icon), filename=f'{screen_name}-{icon.name}')


@root.route('/save-tweets', {'GET', 'POST', 'OPTIONS'})
async def save_tweets(request: Request) -> HTTPResponse:
    check_root_pass(request)
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    try:
        await __save_user_timeline(request, screen_name)
        return text('success.')
    except MySQLError:
        raise ServerError('Failed to save user timeline to database.')
    except mzk.TweepError:
        raise ServerError('Failed to get user timeline from twitter.')


@root.route('/get-tweets', {'GET', 'POST', 'OPTIONS'})
async def get_tweets(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    info = await __get_info(request, screen_name)
    return json(
        await request.app.mysql.execute_aio(core.GET_TWEETS_QUERY, (info.get('id', 0),))
    )


@root.route('/check-saved-tweets-count', {'GET', 'POST', 'OPTIONS'})
async def check_saved_tweets_count(request: Request) -> HTTPResponse:
    screen_name, *_ = mzk.get_args(
        request,
        ('screen_name|name', str, None, {'max_length': 32}),
    )
    if screen_name is None:
        raise Forbidden('screen_name parameter format error.')
    info = await __get_info(request, screen_name)
    res = (await request.app.mysql.execute_aio(core.COUNT_TWEETS_QUERY, (info.get('id', 0),)))[0]
    if len(res) > 0:
        count = res[0]
        return text(str(count))
    else:
        return text('0')


# -------------------------------------------------------------------------- Blueprint --
