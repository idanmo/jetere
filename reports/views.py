
from django.shortcuts import render

from . import models


def _get_jobs():
    return models.Job.objects.all().order_by('name')


def index(request):
    return render(request, 'main.html', {'jobs': _get_jobs()})


def builds(request, job_id):
    # TODO: builds with building=True should have some indication.
    job = models.Job.objects.all().get(id=job_id)
    builds = models.Build.objects.all().filter(
            job_id=job_id).order_by('-number')
    return render(request, 'builds.html', {
        'current_job': job,
        'jobs': _get_jobs(),
        'builds': builds})


def tests(request, build_id):
    build = models.Build.objects.get(id=build_id)
    build_tests = models.Test.objects.all().filter(build_id=build_id)
    suites = {}
    for t in build_tests:
        suite_name = t.name.split('@')[1].strip() if '@' in t.name else t.name
        if suite_name not in suites:
            suites[suite_name] = []
        suites[suite_name].append(t)
    return render(request, 'tests.html', {
        'current_job': build.job,
        'current_build': build,
        'jobs': _get_jobs(),
        'suites': suites
    })


def logs(request, test_id):
    test_logs = models.TestLogs.objects.get(test_id=test_id)
    return render(request, 'logs.html', {
        'current_job': test_logs.test.build.job,
        'current_build': test_logs.test.build,
        'jobs': _get_jobs(),
        'current_test': test_logs.test,
        'test_logs': test_logs
    })
