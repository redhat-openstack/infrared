import ssl
import jenkins

from cli import logger

LOG = logger.LOG


class JenkinsRunner(object):
    """
    The jenkins job runner.

    Starts jenkins jobs using Jenkins python API.
    """
    START_TIMEOUT = 10
    BUILD_COMPLETION_TIMEOUT = 60*60*3
    START_PULL = 1

    def __init__(self, auth_info, ignore_ssh_warnings=True):
        self.host = auth_info.get('url')
        self.username = auth_info.get('username', None)
        self.password = auth_info.get('password', None)

        self.server = jenkins.Jenkins(
            self.host,
            username=self.username,
            password=self.password)
        # ignore ssl warnings
        if ignore_ssh_warnings:
            ssl._create_default_https_context = ssl._create_unverified_context
        self.test_connection()

    def build(self, job_name, job_parameters):
        """
        Starts the job build.

        """
        LOG.debug("Starting job '{}' on '{}' server...".format(
            job_name, self.host))

        self.server.build_job(job_name, job_parameters)
        LOG.debug('Build has started or queued. Check job url: {}'.format(
            self.get_job_info(job_name)['url']))

    def get_build_info(self, job_name, build_number):
        """
        Get the build information
        """

        return self.server.get_build_info(job_name, build_number)

    def get_job_info(self, job_name):
        """
        Gets the job information
        """
        return self.server.get_job_info(job_name)

    def test_connection(self):
        """
        Tests the server connection
        """
        self.server.get_version()
