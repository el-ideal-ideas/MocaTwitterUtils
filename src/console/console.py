# -- Imports --------------------------------------------------------------------------

from sanic import __version__
from sys import version_info
from pymysql import IntegrityError
from subprocess import CalledProcessError
from .. import moca_modules as mzk
from .. import core

# -------------------------------------------------------------------------- Imports --

# -- Console --------------------------------------------------------------------------

console = mzk.typer_console


@console.command('version')
def version(only_number: bool = False) -> None:
    """Show the version info of MocaSystem."""
    if only_number:
        mzk.tsecho(core.VERSION)
    else:
        mzk.tsecho(f'MocaTwitterUtils ({core.VERSION})')


@console.command('update')
def update() -> None:
    """Update modules."""
    path = mzk.TMP_DIR.joinpath('moca_commands_installed_modules.txt')
    mzk.call(f'{mzk.executable} -m pip freeze > {path}', shell=True)
    mzk.call(f'{mzk.executable} -m pip uninstall -r {path} -y', shell=True)
    mzk.install_requirements_file(core.TOP_DIR.joinpath('requirements.txt'))


@console.command('update-system')
def update_system() -> None:
    """Update system, get latest code from github."""
    mzk.update_use_github(
        core.TOP_DIR,
        'https://github.com/el-ideal-ideas/MocaTwitterUtils',
        [
            core.CONFIG_DIR,
            core.LOG_DIR,
            core.STORAGE_DIR,
            core.TOP_DIR.joinpath('keep'),
            core.TOP_DIR.joinpath('atexit.py'),
            core.TOP_DIR.joinpath('atexit.sh'),
            core.TOP_DIR.joinpath('startup.py'),
            core.TOP_DIR.joinpath('startup.sh'),
        ]
    )


@console.command('reset-system')
def reset_system() -> None:
    """Reset this system."""
    mzk.update_use_github(
        core.TOP_DIR,
        'https://github.com/el-ideal-ideas/MocaTwitterUtils',
        []
    )


@console.command('run')
def run(sleep: float = 0) -> None:
    """Run MocaTwitterUtils."""
    try:
        mzk.sleep(sleep)
        # run startup script.
        mzk.call(f'{mzk.executable} "{core.TOP_DIR.joinpath("startup.py")}"', shell=True)
        mzk.call(
            f'chmod +x "{core.TOP_DIR.joinpath("startup.sh")}";sh "{core.TOP_DIR.joinpath("startup.sh")}"', shell=True
        )
        from ..server import moca_sanic
        moca_sanic.run()
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as error:
        mzk.print_critical(str(error))
        mzk.print_exc()
        mzk.append_str_to_file(core.LOG_DIR.joinpath('critical.log'), str(error))
        mzk.append_str_to_file(core.LOG_DIR.joinpath('critical.log'), mzk.format_exc())
    finally:
        # run atexit script.
        mzk.call(f'{mzk.executable} "{core.TOP_DIR.joinpath("atexit.py")}"', shell=True)
        mzk.call(
            f'chmod +x "{core.TOP_DIR.joinpath("atexit.sh")}";sh "{core.TOP_DIR.joinpath("atexit.sh")}"', shell=True
        )


@console.command('start')
def start(sleep: float = 0) -> None:
    """Run MocaTwitterUtils in background."""
    mzk.sleep(sleep)
    mzk.call(
        f'nohup {mzk.executable} {core.TOP_DIR.joinpath("moca.py")} run &> /dev/null &',
        shell=True
    )


@console.command('stop')
def stop(sleep: float = 0) -> None:
    """Stop MocaTwitterUtils."""
    mzk.sleep(sleep)
    pid = []
    for line in mzk.check_output('ps -ef | grep MocaTwitterUtils', shell=True).decode().splitlines():
        pid.append(line.split()[1])
    mzk.call(f'kill {" ".join(pid)} &> /dev/null &', shell=True)


@console.command('restart')
def restart(sleep: float = 0) -> None:
    """Restart MocaTwitterUtils."""
    mzk.sleep(sleep)
    mzk.call(f'nohup {mzk.executable} {core.TOP_DIR.joinpath("moca.py")} stop &> /dev/null &', shell=True)
    mzk.sleep(3)
    mzk.call(f'nohup {mzk.executable} {core.TOP_DIR.joinpath("moca.py")} start &> /dev/null &', shell=True)
    mzk.sleep(3)


@console.command('status')
def show_running_process() -> None:
    """Show all MocaTwitterUtils process."""
    print('++++++++++++++++++++++++++++++++++++++++++++++')
    print(f'Python: {version_info.major}.{version_info.minor}.{version_info.micro}')
    print(f'MocaSystem: {core.VERSION}')
    print(f'MocaModules: {mzk.VERSION}')
    print(f'MocaSanic: {mzk.MocaSanic.VERSION}')
    print(f'Sanic: {__version__}')
    print('++++++++++++++++++++++++++++++++++++++++++++++')
    print('PID\tPPID\tNAME')
    for line in mzk.check_output('ps -ef | grep MocaTwitterUtils', shell=True).decode().splitlines():
        items = line.split()
        if items[7].startswith('MocaTwitterUtils'):
            print(f"{items[1]}\t{items[2]}\t{' '.join(items[7:])}")
    print('++++++++++++++++++++++++++++++++++++++++++++++')


@console.command('turn-on')
def turn_on() -> None:
    """Stop maintenance mode."""
    core.system_config.set_config('maintenance_mode', False)
    mzk.tsecho('Stopped maintenance mode. MocaSanic is working.', fg=mzk.tcolors.GREEN)


@console.command('turn-off')
def turn_off() -> None:
    """Start maintenance mode."""
    core.system_config.set_config('maintenance_mode', True)
    mzk.tsecho('MocaSystem is currently undergoing maintenance. All requests will receive 503.', fg=mzk.tcolors.GREEN)


@console.command('clear-logs')
def clear_logs() -> None:
    """Clear log files."""
    mzk.call(f'rm -rf {core.LOG_DIR}/*', shell=True)


@console.command('save-tweets')
def save_tweets(screen_name: str) -> None:
    """Save latest tweets to database."""
    info = core.moca_twitter.get_user_info(screen_name)
    user_id = info.get('id', 0)
    try:
        core.cursor.execute(
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
        )
    except IntegrityError:
        core.cursor.execute(
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
            )
        )
    finally:
        core.mysql.commit()
    try:
        for tweet in core.moca_twitter.get_timeline(
                screen_name, count=200, exclude_replies=False, include_rts=True, include_entities=True
        ):
            data = tweet._json
            try:
                core.cursor.execute(
                    core.INSERT_TWEET_QUERY,
                    (data['id'],
                     user_id,
                     data['text'],
                     data['created_at'],
                     data['source'].split('>')[1].split('<')[0])
                )
            except IntegrityError:
                pass
        core.mysql.commit()
    except mzk.TweepError:
        mzk.sys_exit(1)


@console.command('update-tweets')
def update_tweets() -> None:
    """Save latest tweets to database. for all accounts in configs/screen_name.json"""
    screen_name_list = mzk.load_json_from_file(core.CONFIG_DIR.joinpath('screen_name.json'))
    for screen_name in screen_name_list:
        try:
            mzk.call(f'{mzk.executable} "{core.TOP_DIR.joinpath("moca.py")}" save-tweets {screen_name}', shell=True)
            mzk.tsecho(f"Update tweets successfully -- {screen_name}", fg=mzk.tcolors.GREEN)
            mzk.sleep(60)
        except CalledProcessError:
            mzk.tsecho(
                f"Update tweets failed, system will try again in 300 seconds-- {screen_name}", fg=mzk.tcolors.YELLOW
            )
            mzk.sleep(300)
            try:
                mzk.call(f'{mzk.executable} "{core.TOP_DIR.joinpath("moca.py")}" save-tweets {screen_name}', shell=True)
                mzk.tsecho(f"Update tweets successfully -- {screen_name}", fg=mzk.tcolors.GREEN)
                mzk.sleep(60)
            except CalledProcessError:
                mzk.tsecho(f"Update tweets failed -- {screen_name}", fg=mzk.tcolors.RED)
            
            
@console.command('save-tweets-to-file')
def save_tweets_to_file(screen_name: str, filename: str) -> None:
    """Get all tweets from database and save to a file."""
    core.cursor.execute(
        core.SCREEN_NAME_TO_ID_QUERY,
        (screen_name,)
    )
    res = core.cursor.fetchall()[0]
    if len(res) > 0:
        core.cursor.execute(
            core.GET_TWEETS_QUERY,
            (res[0],)
        )
        res = core.cursor.fetchall()
        with open(filename, mode='w') as file:
            for item in res:
                file.write(item[2])
                file.write('\n')
    else:
        mzk.tsecho(f"Unknown screen_name", fg=mzk.tcolors.RED)


@console.command('__keep-update-tweets', hidden=True)
def __keep_update_tweets(interval: int) -> None:
    """run update-tweets command with interval on background."""
    mzk.set_process_name(f'MocaTwitterUtils({core.VERSION}) -- keep-update-tweets')
    while True:
        mzk.call(
            f'nohup {mzk.executable} "{core.TOP_DIR.joinpath("moca.py")}" update-tweets &> /dev/null &', shell=True
        )
        mzk.sleep(interval)


@console.command('keep-update-tweets')
def keep_update_tweets(interval: int) -> None:
    """run update-tweets command with interval on background."""
    mzk.call(
        f'nohup {mzk.executable} "{core.TOP_DIR.joinpath("moca.py")}" __keep-update-tweets {interval} &> /dev/null &', shell=True
    )

# -------------------------------------------------------------------------- Console --
