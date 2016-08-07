
import datetime
import json
import time

from django.core.management.base import BaseCommand, CommandError
from django.core import exceptions
from django.utils import timezone

import jenkins

from reports import models


# TODO: should be configurable in DB (maybe per job).
BUILDS_HISTORY_LIMIT = 10


class Command(BaseCommand):
    help = 'Sync database with Jenkins'

    @staticmethod
    def _extract_started_by(jenkins_build):
        actions = jenkins_build.get('actions', [])
        for action in actions:
            causes = action.get('causes', [])
            for cause in causes:
                description = cause['shortDescription']
                if 'Started by timer' in description:
                    return 'Timer'
                elif 'Started by' in description:
                    return description.replace('Started by user', '').strip()
        return None

    @staticmethod
    def _process_build_tests(raw_test_report, build):
        suites = raw_test_report.get('suites', [])
        tests_count = 0
        for suite in suites:
            # TODO: try except
            cases = suite.get('cases', [])
            for case in cases:
                test = models.Test()
                test.duration = datetime.timedelta(
                        seconds=int(case['duration']))
                test.class_name = case['className']
                test.status = case['status']
                test.name = case['name']
                test.build_id = build.id
                test.save()
                tests_count += 1

                models.TestLogs(
                    test_id=test.id,
                    error_stack_trace=case['errorStackTrace'],
                    stdout=case['stdout'],
                    stderr=case['stderr']
                ).save()

        return tests_count

    @staticmethod
    def _get_jenkins_configuration():
        configuration = models.Configuration.objects.all()
        if len(configuration) == 0:
            raise CommandError('Jenkins configuration not found in DB.')
        if len(configuration) > 1:
            raise CommandError('There is more than one Jenkins configuration '
                               'in DB. remove unused configurations.')
        return configuration[0]

    def handle(self, *args, **options):
        start_time = time.time()

        config = self._get_jenkins_configuration()
        self.stdout.write(
                self.style.SUCCESS('Jenkins configuration found in DB.'))

        self.stdout.write('Jenkins URL: %s' % config.jenkins_url)
        self.stdout.write('Jenkins username: %s, password: *****'
                          % config.jenkins_username)

        # TODO: rest call for verifying jenkins connectivity
        self.stdout.write(self.style.SUCCESS(
                'Connection to Jenkins server established.'))

        jobs = models.Job.objects.all()

        errors = []

        self.stdout.write('The following jobs will be processed:')
        for job in jobs:
            self.stdout.write(' - %s' % job)
        for job in jobs:
            self.stdout.write('')
            self.stdout.write('** Processing job: %s' % job)
            server = jenkins.Jenkins(config.jenkins_url,
                                     config.jenkins_username,
                                     config.jenkins_password)
            try:
                jenkins_job = server.get_job(job.jenkins_path,
                                             tree='displayName,builds[number]')
                display_name = jenkins_job['displayName']
                jenkins_builds = [x['number'] for x in jenkins_job['builds']]
                if job.name != display_name:
                    job.name = display_name
                    job.save()
                    self.stdout.write('Updated job.id=%d name to "%s"'
                                      % (job.id, display_name))
            except Exception as e:
                errors.append('Error processing job [%s]: %s - %s'
                              % (job, e.__class__.__name__, e.message))
                self.stdout.write(self.style.ERROR(errors[-1]))

            # update in progress builds
            in_progress_builds = models.Build.objects.filter(job_id=job.id,
                                                             building=True)
            self.stdout.write('Found in progress builds: %s'
                              % json.dumps(
                                [x.number for x in in_progress_builds]))
            if in_progress_builds:
                self.stdout.write('Processing in progress builds..')
                for build in in_progress_builds:
                    self._process_build(
                            build.number, errors, job, server, update=True)

            builds_to_update = []
            for build_number in jenkins_builds[:BUILDS_HISTORY_LIMIT]:
                try:
                    models.Build.objects.get(job_id=job.id,
                                             number=build_number)
                except exceptions.ObjectDoesNotExist:
                    builds_to_update.append(build_number)
            self.stdout.write(
                    'The following new builds will be synced from jenkins: %s'
                    % json.dumps(builds_to_update))

            for build_number in builds_to_update:
                self._process_build(build_number, errors, job, server)

        # TODO: store errors in DB.
        if errors:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('Errors summary:'))
            for error in errors:
                self.stdout.write('- %s' % error)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
                'Sync done in %s seconds.' % (time.time() - start_time)))

    def _process_build(self, build_number, errors, job, server, update=False):
        self.stdout.write('Processing build #%d..' % build_number)
        try:
            # TODO: add tree=... to get_build invocation
            jenkins_build = server.get_build(job.jenkins_path,
                                             build_number)
            if update:
                build = models.Build.objects.get(job_id=job.id,
                                                 number=build_number)
            else:
                build = models.Build()
            build.duration = datetime.timedelta(
                    milliseconds=jenkins_build['duration'])
            build.number = build_number
            build.result = jenkins_build['result']

            build.timestamp = timezone.make_aware(
                    datetime.datetime.fromtimestamp(
                            int(jenkins_build['timestamp']) / 1000),
                    timezone.get_current_timezone())

            build.started_by = self._extract_started_by(jenkins_build)
            build.building = jenkins_build['building']
            build.job = job
            build.save()

            build = models.Build.objects.get(job_id=job.id,
                                             number=build.number)
            if build.building:
                self.stdout.write(' - Build in "building" state, '
                                  'not processing tests.')
            else:
                report = server.get_tests_report(job.jenkins_path,
                                                 build.number)
                tests_count = self._process_build_tests(report, build)
                self.stdout.write(' - Added %d tests.' % tests_count)

        except Exception as e:
            errors.append(
                    'Error processing build number %d for job [%s]: '
                    '%s - %s' % (build_number,
                                 job,
                                 e.__class__.__name__,
                                 e.message))
            self.stdout.write(self.style.ERROR(errors[-1]))
