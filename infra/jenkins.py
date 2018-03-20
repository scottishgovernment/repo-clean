from string import Template

import requests

from .utils import python_date_from_javascript_timestamp


class Jenkins():
    def __init__(self, host):
        self.host = host
        # self.verbose = verbose

    def build_date(self, job_name, version):
        jsn = self._get_build_json(job_name, version)
        assert jsn['result'] == "SUCCESS"
        javascript_timestamp = jsn['timestamp']
        return python_date_from_javascript_timestamp(javascript_timestamp)

    def _get_build_json(self, job_name, version):
        url = self.build_url(job_name, version)
        return requests.get(url).json()

    def build_url(self, job_name, version):
        params = {
            "jenkins_host": self.host,
            "job_name": job_name,
            "version": version,
        }
        url_template = Template(
            "http://$jenkins_host/job/$job_name/$version/api/json")
        url = url_template.substitute(params)
        return url


# eof
