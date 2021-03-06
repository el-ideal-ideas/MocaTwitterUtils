#!/usr/bin/env python3

"""
A console utility to backup the file or directory.

Requirements
------------
schedule
docopt
"""

# -- Imports --------------------------------------------------------------------------
from sys import executable
from subprocess import call
from time import sleep
from shutil import make_archive
from os import remove
from datetime import datetime
from glob import glob
from pathlib import Path
try:
    from docopt import docopt
    from schedule import every, run_pending
except (ImportError, ModuleNotFoundError):
    call(f"{executable} -m pip install --upgrade pip docopt schedule", shell=True)
    from docopt import docopt
    from schedule import every, run_pending

# -------------------------------------------------------------------------- Imports --

# -- Variables --------------------------------------------------------------------------

__doc__ = """

    This is a console utility to backup the file or directory.

    Usage:
        backup.py <target> <save_to> <limits> <time>
        backup.py --help | -h
        backup.py --license

    Example:
        backup.py /var/www/html /root/backup/web/ 5 604800
            this command will save all file in /var/www/html to /root/backup/web/ per 604800 seconds (7days).
            if the number of the backup file is more than 5, the most oldest file will be removed.
"""

# -------------------------------------------------------------------------- Variables --

# -- Main --------------------------------------------------------------------------


args = docopt(__doc__)

if args['-h'] or args['--help']:
    print(__doc__)
elif args['--license']:
    print("""
MIT License

Copyright 2020.5.28 <el.ideal-ideas: https://www.el-ideal-ideas.com>

Permission is hereby granted, free of charge, to any person obtaining 
a copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies 
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE 
AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    """)
elif args['<target>'] and args['<save_to>'] and args['<limits>'] and args['<time>']:
    save_to = str(Path(args['<save_to>']).absolute()) + '/'
    target = str(Path(args['<target>']).absolute()) + '/'
    Path(save_to).mkdir(parents=True, exist_ok=True)

    def job():
        make_archive(
            save_to + str(datetime.now()) + '-backup',
            'zip',
            root_dir=target
        )
        files = glob(save_to + '*' + '-backup.zip')
        if len(files) > int(args['<limits>']):
            oldest = None
            for file in files:
                date = datetime.fromisoformat(file[len(save_to):-11])
                if (oldest is None) or (date < oldest):
                    oldest = date
            remove(save_to + str(oldest) + '-backup.zip')

    every(int(args['<time>'])).seconds.do(job)

    while True:
        run_pending()
        sleep(1)
else:
    print('usage error.')

# -------------------------------------------------------------------------- Main --
