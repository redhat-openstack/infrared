import yaml
import datetime
import time
import json
import urllib
import urllib3
import fnmatch
import os
from contextlib import closing


def is_ok_resp_code(code):
    return code >= 200 and code < 300


class ClientContext(object):
    def __init__(self, spec):
        self.spec = spec
        self.token_response = None
        connection_pool_kw = {}
        if 'ca_cert' in spec:
            connection_pool_kw['ca_certs'] = spec['ca_cert']
        if 'validate_certs' in spec:
            if not spec['validate_certs']:
                connection_pool_kw['cert_reqs'] = 'CERT_NONE'
        if 'api_timeout' in spec:
            connection_pool_kw['timeout'] = spec['api_timeout']
        else:
            connection_pool_kw['timeout'] = spec.get('timeout', 180)

        if 'client_key' in spec:
            connection_pool_kw['key_file'] = spec['client_key']

        if 'client_cert' in spec:
            connection_pool_kw['cert_file'] = spec['client_cert']

        self.http = urllib3.PoolManager(**connection_pool_kw)

    def request(self, **kwargs):
        return self.http.request(**kwargs)

    def authenticated_request(self, **kwargs):
        token = self.get_token()
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['X-Auth-Token'] = token
        return self.http.request(**kwargs)

    # somple os request
    def authenticated_json_request(self, endpoint, rel_url, method, body=None):
        if body is not None:
            json_data = json.dumps(body).encode('utf-8')
        else:
            json_data = ''
        base_url = self.endpoint_for(endpoint)

        response = self.authenticated_request(method=method,
                                              url=base_url+rel_url,
                                              headers={
                                                  'Content-Type': 'application/json'},
                                              body=json_data
                                              )

        if not is_ok_resp_code(response.status):
            raise RuntimeError("unexpected status {} on token get, response: {}".
                               format(response.status, response.data))
        return json.loads(response.data.decode('utf-8'))

    def has_non_expired_token(self):
        ret = None
        # currently using a 30 min timeout
        # instead of checking the headers / expires
        if self.token_response:
            if self.token_response['time'] + 1800.0 < time.time():
                return None
            if 'X-Subject-Token' in self.token_response['headers']:
                ret = self.token_response

        return ret

    def get_keystone_url(self):
        return 'https://rhos-d.infra.prod.upshift.rdu2.redhat.com:13000/v3'

    def loopup_cloud(self, cloud):
        paths = ['clouds.yaml', os.path.expanduser(
            '~/.config/openstack/clouds.yaml'), '/etc/openstack/clouds.yaml']
        for path in paths:
            try:
                with closing(open(path, 'r')) as f:
                    data = yaml.load(f, yaml.SafeLoader)
                    if 'clouds' in data:
                        data = data['clouds']
                        if cloud in data:
                            return data[cloud]
            except (FileNotFoundError, PermissionError):
                pass
        raise RuntimeError("Failed to find {} in **clouds.yaml".format(cloud))

    def fetch_token(self):
        if 'cloud' in self.spec and ('auth' not in self.spec or not self.spec['auth']):
            section = self.loopup_cloud(self.spec['cloud'])
            self.spec['auth'] = section['auth']

        auth = self.spec['auth']
        if 'auth_url' not in auth:
            raise RuntimeError(
                "Unable to determine the auth_url, missing argumet")
        auth_url = auth['auth_url']
        if '/v3' not in auth_url:
            auth_url += '/v3'

        # missing auth params will raise
        # some of them may get an user friendlier error message in the future

        # user identified with user (name or id) + Domain (name or id)
        # project scope domain (name or id)  + project (name or id)
        if 'domain_name' not in auth and 'domain_id' not in auth:
            auth['domain_name'] = 'Default'

        if 'project_domain_name' not in 'auth' and 'project_domain_id' not in auth:
            if 'domain_name' in auth:
                auth['project_domain_name'] = auth['domain_name']
            else:
                auth['project_domain_id'] = auth['domain_id']

        scope = {}
        if 'project_name' in auth or 'project_id' in auth:
            token_scope = "project"
        else:
            token_scope = "domain"

        if token_scope == "project":
            scope["project"] = {"domain": {}}
            if 'project_domain_name' in auth:
                scope["project"]["domain"]["name"] = auth['project_domain_name']
            else:
                scope["project"]["domain"]["id"] = auth['project_domain_id']
            if 'project_name' in auth:
                scope["project"]["name"] = auth['project_name']
            else:
                scope["project"]["id"] = auth['project_id']
        else:
            scope["domain"] = {}
            if 'project_domain_name' in auth:
                scope["domain"]["name"] = auth['project_domain_name']
            else:
                scope["domain"]["id"] = auth['project_domain_id']

        user = {}
        if 'username' in auth:
            user["name"] = auth['username']
        else:
            user["id"] = auth['user_id']
        if 'domain_name' in auth:
            user["domain"] = {"name": auth["domain_name"]}
        else:
            user["domain"] = {"id": auth["domain_id"]}
        user["password"] = auth["password"]

        auth = {"auth": {"identity": {
            "methods": ["password"],
            "password": {
                "user": user
            }},
            "scope": scope
        }}

        json_data = json.dumps(auth).encode('utf-8')
        response = self.request(method='POST',
                                url=auth_url + '/auth/tokens',
                                headers={'Content-Type': 'application/json'},
                                body=json_data)
        invalid = None
        try:
            self.token_response = {}
            self.token_response['data'] = json.loads(
                response.data.decode('utf-8'))
            self.token_response['headers'] = response.headers
            self.token_response['time'] = time.time()
            # based on service type, may switch to service name
            self.catalog = {}
            for entry in self.token_response['data']['token']['catalog']:
                service_type = entry['type']
                if 'endpoints' in entry:
                    for enp in entry['endpoints']:
                        interface = enp['interface']
                        region = enp['region']
                        url = enp['url']
                        if url[-1] == '/':
                            url = url[0:-1]
                        if region not in self.catalog:
                            self.catalog[region] = {}
                        if interface not in self.catalog[region]:
                            self.catalog[region][interface] = {}
                        self.catalog[region][interface][service_type] = url
        except json.decoder.JSONDecodeError:
            invalid = True

        if not is_ok_resp_code(response.status):
            raise RuntimeError("unexpected status {} on token get, response: {}".
                               format(response.status, response.data))
        if invalid:
            raise RuntimeError("Non json response {}".
                               format(response.data))

    def get_token(self):
        ret = self.has_non_expired_token()
        if ret:
            return ret['headers']['X-Subject-Token']
        self.fetch_token()

        return self.has_non_expired_token()['headers']['X-Subject-Token']

    # KeyError, RuntimeError on missing
    def endpoint_for(self, endpoint_type):
        if not hasattr(self, 'catalog'):
            self.get_token()
        if 'region_name' not in self.spec and len(self.catalog) > 1:
            raise RuntimeError(
                "Multiple region avalible, regison must be specified!")
        else:
            self.spec['region_name'] = next(iter(self.catalog))
        interface = self.spec.get('interface', 'public')
        if isinstance(endpoint_type, str):
            return self.catalog[self.spec['region_name']][interface][endpoint_type]
        else:
            for enp in endpoint:
                try:
                    base_url = self.endpoint_for(endpoint)
                    return self.catalog[self.spec['region_name']][interface][endpoint_type]
                except KeyError:
                    pass
        raise RuntimeError("Failed to find url for endpoint {}", endpoint_type)

    def compute_request(self, **kwargs):
        return self.authenticated_json_request(endpoint='compute', **kwargs)

    def compute_server_search(self, server=None, detailed=False, filters=None, all_projects=False):
        url = '/servers'
        params = filters
        if filters is not None:
            params = filters.copy()
        if all_projects:
            params['all_projects'] = ''

        if detailed:
            url += '/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        servers = self.compute_request(method='GET', rel_url=url)
        openstack_servers = servers['servers']
        openstack_servers = [srv for srv in openstack_servers
                             if fnmatch.fnmatch(srv['name'], server) or fnmatch.fnmatch(srv['id'], server)]
        return openstack_servers


def openstack_full_argument_spec(**kwargs):
    spec = dict(
        cloud=dict(default=None, type='raw'),
        auth_type=dict(default=None),  # ignored
        auth=dict(default=None, type='dict', no_log=True),
        region_name=dict(default=None),
        availability_zone=dict(default=None),  # ignored
        validate_certs=dict(default=None, type='bool', aliases=[
                            'verify']),  # default to false ?
        ca_cert=dict(default=None, aliases=['cacert']),
        client_cert=dict(default=None, aliases=['cert']),
        client_key=dict(default=None, no_log=True, aliases=['key']),
        # implementation is module dependent
        wait=dict(default=True, type='bool'),
        timeout=dict(default=180, type='int'),
        api_timeout=dict(default=None, type='int'),
        interface=dict(
            default='public', choices=['public', 'internal', 'admin'],
            aliases=['endpoint_type']),
    )
    spec.update(kwargs)
    return spec
