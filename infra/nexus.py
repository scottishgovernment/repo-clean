from os import environ
from string import Template
from io import BytesIO

import requests
from lxml import etree
from yaml import load


class Nexus():
    def __init__(self, host):
        self.host = host
        self.auth = (environ['NEXUS_USER'], environ['NEXUS_PASSWORD'])

    def _full_url(self, path):
        return 'http://' + self.host + path

    def product_maven_metadata(self, component_name):
        release = "scot/mygov/release"
        params = {"release": release, "component_name": component_name}
        url_template = Template(
            "/repository/releases/$release/$component_name/maven-metadata.xml")
        url = self._full_url(url_template.substitute(params))
        r = requests.get(url)
        if r.status_code != 200:
            raise RuntimeError("Nexus on %s returns %s: %s" %
                               (self.host, r.status_code, r.reason))

        xml = r.text
        tree = etree.parse(BytesIO(xml.encode('utf8')))
        return tree

    def product_release_yaml(self, group_name, product_name, release):
        """Return the yaml for a specific product release in json format."""
        group_path = group_name.replace('.', '/')
        params = {
            'group': group_path,
            'product': product_name,
            'version': release,
        }
        path_template = Template("/repository/releases/$group" +
                                 "/$product/$version/$product-$version.yaml")
        path = path_template.substitute(params)
        url = self._full_url(path)
        # if self.args.verbose:
        #     print("url: %s" % url)
        r = requests.get(url)
        if r.status_code != 200:
            raise RuntimeError("Nexus %s: returns %s : %s\n%s" %
                               (self.host, r.status_code, r.reason, url))
        txt = r.text
        jsn = load(txt)
        return jsn

    def _get_items(self, path, auth=None, params={}):
        url = self._full_url(path)
        while True:
            r = requests.get(url=url, auth=auth, params=params)
            if r.status_code != 200:
                raise RuntimeError("Nexus %s returning %s: %s\n%s" %
                                   (self.host, r.status_code, r.reason, url))
            assert r.status_code == 200
            jsn = r.json()
            items = jsn['items']
            if not items:
                break
            for item in items:
                yield (item)

            cont = jsn['continuationToken']
            if not cont:
                break

            params['continuationToken'] = cont

    def list_tasks(self):
        path = "/service/rest/beta/tasks"
        return self._get_items(path=path, auth=self.auth)

    def search(self, groupId, artefactId=None, version=None):
        # if self.args.verbose:
        #     print("nexus search: group %s artefact %s version %s" %
        #           (groupId, artefactId, version))
        params = {
            "repository": 'releases',
            "group": groupId,
            'name': artefactId,
            'version': version,
        }
        path = "/service/rest/beta/search"
        results = self._get_items(path=path, params=params)
        return results

    def artefact_versions(self, groupId, artefactId):
        results = self.search(groupId=groupId, artefactId=artefactId)
        versions = [x['version'] for x in results]
        return versions

    def related_artefactIds(self, groupId, version):
        results = self.search(groupId=groupId, version=version)
        artifactIds = [x['name'] for x in results]
        return artifactIds

    def delete_gav_and_its_assets(self, gav):
        (g, a, v) = gav.abbrevs
        items = [x for x in self.search(groupId=g, artefactId=a, version=v)]
        print("Deleting %s" % gav)
        num = len(items)
        if num == 0:
            print("%s does not exist, cannot delete" % gav)
            return
        assert (num == 1)
        component = items[0]
        component_id = component['id']
        self.delete_component(component_id)

    def _delete(self, thing_type, thing_id):
        assert thing_type in ['assets', 'components']
        path = "/service/rest/beta/%s/%s" % (thing_type, thing_id)
        url = self._full_url(path)
        print(url)

        r = requests.delete(url=url, auth=self.auth)
        assert r.status_code == 204

    def delete_asset(self, asset_id):
        return self._delete('assets', asset_id)

    def delete_component(self, component_id):
        return self._delete('components', component_id)

    def compact_blobstore(self):
        tasks = self.list_tasks()
        compact_task_id = None
        for task in tasks:
            if task['type'] == 'blobstore.compact':
                compact_task_id = task['id']
        assert compact_task_id is not None
        path = '/service/rest/beta/tasks/%s/run' % compact_task_id
        url = self._full_url(path)
        r = requests.post(url, auth=self.auth)
        assert r.status_code == 204


# eof
