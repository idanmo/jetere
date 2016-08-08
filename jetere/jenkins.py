
import requests


class Jenkins(object):

    def __init__(self, base_url, username=None, password=None):
        self._base_url = base_url
        self._username = username
        self._password = password

    def get_job(self, job_name, tree=None):
        resource = '{}/job/{}/api/json?tree={}'.format(
                self._base_url,
                job_name.replace('/', '/job/'),
                '' if tree is None else tree)
        response = requests.get(resource,
                                auth=(self._username, self._password))
        return response.json()

    def get_build(self, job_name, build_number, tree=None):
        resource = '{}/job/{}/{}/api/json?{}'.format(
                self._base_url,
                job_name.replace('/', '/job/'),
                build_number,
                '' if tree is None else 'tree=%s' % tree)
        response = requests.get(resource,
                                auth=(self._username, self._password))
        return response.json()

    def get_tests_report(self, job_name, build_number):
        resource = '{}/job/{}/{}/testReport/api/json'.format(
                self._base_url,
                job_name.replace('/', '/job/'),
                build_number)
        response = requests.get(resource,
                                auth=(self._username, self._password))
        if response.status_code != 200:
            raise IOError('Request for resource: "%s" status code = %d'
                          % (resource, response.status_code))
        return response.json()
