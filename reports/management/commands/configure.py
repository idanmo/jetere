import json
import os

from django.core.management.base import BaseCommand

from reports import models

CONFIG_DIR_PATH = os.path.expanduser('~/.jetere')
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, 'config.json')


class Command(BaseCommand):
    help = 'Configure jetere'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--jenkins-url',
                            required=True,
                            type=str,
                            help='Jenkins URL')
        parser.add_argument('--jenkins-username',
                            required=True,
                            type=str,
                            help='Jenkins username')
        parser.add_argument('--jenkins-password',
                            required=True,
                            type=str,
                            help='Jenkins username')

    def handle(self, *args, **options):
        config = {
            'jenkins_url': options['jenkins_url'],
            'jenkins_username': options['jenkins_username'],
            'jenkins_password': options['jenkins_password'],
        }

        if not os.path.exists(CONFIG_DIR_PATH):
            os.makedirs(CONFIG_DIR_PATH)

        self.stdout.write('Writing configuration to %s' % CONFIG_FILE_PATH)

        with open(CONFIG_FILE_PATH, 'w') as f:
            f.write(json.dumps(config, indent=2))

        conf_obj = models.Configuration.objects.all()
        if len(conf_obj) == 0:
            self.stdout.write('Creating a new configuration in DB...')
            conf_obj = models.Configuration()
        else:
            self.stdout.write(
                'Existing configuration found in DB, updating...')
            conf_obj = conf_obj[0]

        conf_obj.jenkins_url = config['jenkins_url']
        conf_obj.jenkins_username = config['jenkins_password']
        conf_obj.jenkins_password = config['jenkins_password']

        conf_obj.save()
        self.stdout.write(self.style.SUCCESS('Done.'))
