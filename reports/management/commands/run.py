import os
import sched
import signal
import time
from subprocess import Popen
from sys import stdout, stdin, stderr

from django.core.management.base import BaseCommand

scheduler = sched.scheduler(time.time, time.sleep)


class Command(BaseCommand):
    help = 'Run jetere!'

    runserver_cmd = 'python manage.py runserver'
    sync_cmd = 'python manage.py sync'

    sync_proc = None

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--sync',
                            action='store_true',
                            help='Synchronize with jenkins every 1 minute.')

    def _sync(self):
        self.sync_proc = Popen(self.sync_cmd,
                               shell=True,
                               stdin=stdin,
                               stdout=stdout,
                               stderr=stderr)
        # scheduler.enter(30, 1, self._sync, ())

    def handle(self, *args, **options):
        runserver_proc = Popen(self.runserver_cmd,
                               shell=True,
                               stdin=stdin,
                               stdout=stdout,
                               stderr=stderr)
        sync_proc = None
        if options['sync']:
            self._sync()
        try:
            while True:
                scheduler.run()
                time.sleep(5)
        except KeyboardInterrupt:
            os.kill(runserver_proc.pid, signal.SIGKILL)
            if sync_proc:
                os.kill(sync_proc.pid, signal.SIGKILL)
