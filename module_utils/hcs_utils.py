# Copyright (c), Google Inc, 2017
# Simplified BSD License (see licenses/simplified_bsd.txt or
# https://opensource.org/licenses/BSD-2-Clause)

import traceback

THIRD_LIBRARIES_IMP_ERR = None
try:
    from keystoneauth1.adapter import Adapter
    from keystoneauth1.identity import v3
    from keystoneauth1 import session
    HAS_THIRD_LIBRARIES = True
except ImportError:
    THIRD_LIBRARIES_IMP_ERR = traceback.format_exc()
    HAS_THIRD_LIBRARIES = False

from ansible.module_utils.basic import (AnsibleModule, env_fallback,
                                        missing_required_lib)
from ansible.module_utils.hwc_utils import (HwcClientException, session_method_wrapper)


class _ServiceClient(object):
    def __init__(self, client, endpoint, product):
        self._client = client
        self._endpoint = endpoint
        self._default_header = {
            'User-Agent': "Huawei-Ansible-MM-%s" % product,
            'Accept': 'application/json',
        }

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, e):
        self._endpoint = e

    @session_method_wrapper
    def get(self, url, body=None, header=None, timeout=None):
        return self._client.get(url, json=body, timeout=timeout,
                                headers=self._header(header))

    @session_method_wrapper
    def post(self, url, body=None, header=None, timeout=None):
        return self._client.post(url, json=body, timeout=timeout,
                                 headers=self._header(header))

    @session_method_wrapper
    def delete(self, url, body=None, header=None, timeout=None):
        return self._client.delete(url, json=body, timeout=timeout,
                                   headers=self._header(header))

    @session_method_wrapper
    def put(self, url, body=None, header=None, timeout=None):
        return self._client.put(url, json=body, timeout=timeout,
                                headers=self._header(header))

    def _header(self, header):
        if header and isinstance(header, dict):
            for k, v in self._default_header.items():
                if k not in header:
                    header[k] = v
        else:
            header = self._default_header

        return header


class Config(object):
    def __init__(self, module, product, verify=True):
        self._project_client = None
        self._domain_client = None
        self._module = module
        self._product = product
        self._verify = verify
        self._endpoints = {}

        self._validate()
        self._gen_provider_client()

    @property
    def module(self):
        return self._module

    def client(self, region, service_type, service_level):
        c = self._project_client
        if service_level == "domain":
            c = self._domain_client

        e = self._get_service_endpoint(c, service_type, region)

        return _ServiceClient(c, e, self._product)

    def _gen_provider_client(self):
        m = self._module
        p = {
            "auth_url": m.params['auth']['auth_url'],
            "password": m.params['auth']['password'],
            "username": m.params['auth']['username'],
            "project_name": m.params['auth']['project_name'],
            "user_domain_name": m.params['auth']['domain_name'],
            "reauthenticate": True
        }

        self._project_client = Adapter(
            session.Session(auth=v3.Password(**p), verify=self._verify),
            raise_exc=False)

        p.pop("project_name")
        self._domain_client = Adapter(
            session.Session(auth=v3.Password(**p), verify=self._verify),
            raise_exc=False)

    def _get_service_endpoint(self, client, service_type, region):
        k = "%s.%s" % (service_type, region if region else "")

        if k in self._endpoints:
            return self._endpoints.get(k)

        url = None
        try:
            url = client.get_endpoint(service_type=service_type,
                                      region_name=region, interface="public")
        except Exception as ex:
            raise HwcClientException(
                0, "Getting endpoint for %s failed, error=%s" % (k, ex))

        if url == "":
            raise HwcClientException(
                0, "Can not find the endpoint for %s" % k)

        if url[-1] != "/":
            url += "/"

        self._endpoints[k] = url
        return url

    def _validate(self):
        if not HAS_THIRD_LIBRARIES:
            self.module.fail_json(
                msg=missing_required_lib('keystoneauth1'),
                exception=THIRD_LIBRARIES_IMP_ERR)


class HcsModule(AnsibleModule):
    def __init__(self, *args, **kwargs):
        arg_spec = kwargs.setdefault('argument_spec', {})

        arg_spec.update(
            auth=dict(type='dict', default=dict(), options=dict(
                auth_url=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['OS_AUTH_URL', 'ANSIBLE_HWC_IDENTITY_ENDPOINT']),
                ),
                username=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['OS_USERNAME', 'ANSIBLE_HWC_USER']),
                ),
                password=dict(
                    required=True, type='str', no_log=True,
                    fallback=(env_fallback, ['OS_PASSWORD', 'ANSIBLE_HWC_PASSWORD']),
                ),
                domain_name=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['OS_DOMAIN_NAME', 'ANSIBLE_HWC_DOMAIN']),
                ),
                project_name=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['OS_PROJECT_NAME', 'ANSIBLE_HWC_PROJECT']),
                )
            )),
            region=dict(
                type='str',
                fallback=(env_fallback, ['OS_REGION_NAME', 'ANSIBLE_HWC_REGION']),
            ),
            id=dict(type='str')
        )

        super(HcsModule, self).__init__(*args, **kwargs)

