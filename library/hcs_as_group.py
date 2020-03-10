#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Huawei
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

###############################################################################
# Documentation
###############################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ["preview"],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: hcs_as_group
description:
    - auto-scaling group management.
short_description: Creates a resource of auto-scaling group in Huawei Cloud Stack
version_added: '2.10'
author: Huawei Inc. (@huaweicloud)
requirements:
    - keystoneauth1 >= 3.6.0
options:
    state:
        description:
            - Whether the given object should exist in Huawei Cloud Stack.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    group_name:
        description:
            - Specifies the name of the AS group. Value requirements consists of 1 to 64
              characters, including letters, digits, underscores(_), and hyphens(-).
        type: str
        required: true
    configuration_id:
        description:
            - Specifies the configuration ID which defines configurations of instances in the AS group.
        type: str
        required: false
    desire_instance_number:
        description:
            - Specifies the expected number of instances. The default value is the minimum number of instances.
              The value ranges from the minimum number of instances to the maximum number of instances.
        type: int
        required: false
    min_instance_number:
        description:
            - Specifies the minimum number of instances. The default value is 0.
        type: int
        required: false
    max_instance_number:
        description:
            - Specifies the maximum number of instances. The default value is 0.
        type: int
        required: false
    cool_down_time:
        description:
            - Specifies the cooling duration (in seconds). The value ranges from 0 to 86400.
        type: int
        default: 900
    available_zones:
        description:
            - Specifies the availability zones in which to create the instances in the autoscaling group.
        type: list
        required: false
    vpc_id:
        description:
            - Specifies the VPC ID.
        type: str
        required: true
    networks:
        description:
            - Specifies the array of one or more network IDs. The system supports up to five networks.
        type: list
        required: true
    security_group:
        description:
            - Specifies the security group ID to associate with the group.
        type: str
        required: false
    health_periodic_audit_time:
        description:
            - Specifies the health check period (in minutes) for instances.
        type: int
        choices: [5, 15, 60, 180]
        default: 5
    instance_terminate_policy:
        description:
            - Specifies the instance removal policy.
        type: str
        choices: ['OLD_CONFIG_OLD_INSTANCE', 'OLD_CONFIG_NEW_INSTANCE', 'OLD_INSTANCE', 'NEW_INSTANCE']
        default: 'OLD_CONFIG_OLD_INSTANCE'
    delete_publicip:
        description:
            - Specifies whether to delete the elastic IP address bound to the instances of AS group
              when deleting the instances.
        type: bool
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create an auto-scaling group
- name: create an auto-scaling group
  hcs_as_groups:
    group_name: "ansible_as_group_test"
    desire_instance_number: 3
    min_instance_number: 1
    max_instance_number: 5
    cool_down_time: 600
    health_periodic_audit_time: 15
    vpc_id: "575f9799-e8d8-46e8-9bfd-17e48bb2a569"
    networks: ["e5efc2c4-095f-4cb5-b6fc-bdeaeed8a08e"]
    security_group: "230be19e-271b-445a-a603-f9b5b25ef96d"
    delete_publicip: True
'''

RETURN = '''
    id:
        description:
            - Specifies the ID of the AS group.
        type: str
        returned: success
'''

from ansible.module_utils.hwc_utils import (
    Config, HwcClientException, HwcModule, are_different_dicts, build_path,
    get_region, is_empty_value, navigate_value, wait_to_finish)


def build_module():
    return HwcModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            group_name=dict(type='str', required=True),
            configuration_id=dict(type='str'),
            desire_instance_number =dict(type='int'),
            min_instance_number =dict(type='int'),
            max_instance_number =dict(type='int'),
            cool_down_time=dict(type='int'),
            health_periodic_audit_time=dict(type='int', choices=[5, 15, 50, 180]),
            available_zones=dict(type='list', elements='str'),
            vpc_id=dict(type='str', required=True),
            networks=dict(type='list', required=True),
            security_group=dict(type='str'),
            instance_terminate_policy=dict(type='str', choices=[
                'OLD_CONFIG_OLD_INSTANCE', 'OLD_CONFIG_NEW_INSTANCE', 'OLD_INSTANCE', 'NEW_INSTANCE']
            ),
            delete_publicip=dict(type='bool'),
        ),
        supports_check_mode=True,
    )


def main():
    """Main function"""

    module = build_module()
    config = Config(module, "as", verify=False)

    try:
        resource = dict()
        if module.params.get('id'):
            # read as group resource by id
            resource = read_resource(config)
        else:
            # search as group resource by name
            v = search_resource(config)
            n = len(v)
            if n > 1:
                raise Exception("Found more than one resource(%s)" % ", ".join([
                    navigate_value(i, ["scaling_group_id"])
                    for i in v
                ]))

            if n == 1:
                module.params['id'] = navigate_value(v[0], ["scaling_group_id"])
                resource = v[0]

        changed = False
        result = dict()
        if module.params['state'] == 'present':
            if not resource:
                if not module.check_mode:
                    result['action'] = "create"
                    create(config)
                changed = True
            else:
                obj = build_identity_object(module)
                if are_different_dicts(obj, resource):
                    if not module.check_mode:
                        result['action'] = "update"
                        update(config)
                    changed = True
        else:
            if resource:
                if not module.check_mode:
                    result['action'] = "delete"
                    delete(config)
                changed = True

    except Exception as ex:
        module.fail_json(msg=str(ex))

    else:
        result['changed'] = changed
        result['id'] = module.params['id']
        module.exit_json(**result)


def build_identity_object(module):
    """
    build resource from input module params
    :param module: input module
    :return: resource object in read response format, missing params equal None
    """
    networks = expand_create_networks(module.params)
    security_groups = expand_create_security_groups(module.params)
    return {
        "scaling_group_id": module.params.get("id"),
        "scaling_group_name": module.params.get("group_name"),
        "scaling_group_status": None,
        "scaling_configuration_id": module.params.get("configuration_id"),
        "desire_instance_number": module.params.get("desire_instance_number"),
        "min_instance_number": module.params.get("min_instance_number"),
        "max_instance_number": module.params.get("max_instance_number"),
        "cool_down_time": module.params.get("cool_down_time"),
        "health_periodic_audit_time": module.params.get("health_periodic_audit_time"),
        "available_zones": module.params.get("available_zones"),
        "vpc_id": module.params.get("vpc_id"),
        "networks": networks,
        "security_groups": security_groups,
        "instance_terminate_policy": module.params.get("instance_terminate_policy"),
        "delete_publicip": module.params.get("delete_publicip"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    params = build_create_parameters(module.params)
    r = send_create_request(module, params, client)
    module.params['id'] = navigate_value(r, ["scaling_group_id"])


def update(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    params = build_update_parameters(module.params)
    r = send_update_request(module, params, client)
    module.params['id'] = navigate_value(r, ["scaling_group_id"])


def delete(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    return send_delete_request(module, None, client)


def read_resource(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    r = send_read_request(module, client)
    res = fill_read_resp_body(r)

    return res


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    identity_obj = build_identity_object(module)
    query_link = build_query_link(module.params)
    link = "scaling_group" + query_link

    result = []
    p = {'start_number': 0}
    while True:
        url = link.format(**p)
        r = send_list_request(module, client, url)
        if not r:
            break

        for item in r:
            item = fill_read_resp_body(item)
            if not are_different_dicts(identity_obj, item):
                result.append(item)

        if len(result) > 1:
            break

        p['start_number'] += 10

    return result


def build_create_parameters(opts):
    """
    - change the input parameters with required name or value format of create API
    - ignore empty parameter
    """

    params = dict()

    v = navigate_value(opts, ["group_name"])
    if not is_empty_value(v):
        params["scaling_group_name"] = v

    v = navigate_value(opts, ["configuration_id"])
    if not is_empty_value(v):
        params["scaling_configuration_id"] = v

    v = navigate_value(opts, ["desire_instance_number"])
    if not is_empty_value(v):
        params["desire_instance_number"] = v

    v = navigate_value(opts, ["min_instance_number"])
    if not is_empty_value(v):
        params["min_instance_number"] = v

    v = navigate_value(opts, ["max_instance_number"])
    if not is_empty_value(v):
        params["max_instance_number"] = v

    v = navigate_value(opts, ["cool_down_time"])
    if not is_empty_value(v):
        params["cool_down_time"] = v

    v = navigate_value(opts, ["health_periodic_audit_time"])
    if not is_empty_value(v):
        params["health_periodic_audit_time"] = v
        params["health_periodic_audit_method"] = "NOVA_AUDIT"

    v = navigate_value(opts, ["available_zones"])
    if not is_empty_value(v):
        params["available_zones"] = v

    v = navigate_value(opts, ["vpc_id"])
    if not is_empty_value(v):
        params["vpc_id"] = v

    v = expand_create_networks(opts)
    if not is_empty_value(v):
        params["networks"] = v

    v = expand_create_security_groups(opts)
    if not is_empty_value(v):
        params["security_groups"] = v

    v = navigate_value(opts, ["instance_terminate_policy"])
    if not is_empty_value(v):
        params["instance_terminate_policy"] = v

    v = navigate_value(opts, ["delete_publicip"])
    if not is_empty_value(v):
        params["delete_publicip"] = v

    return params


def expand_create_networks(d):
    v = d.get("networks")
    if not v:
        return None

    return [{"id": i} for i in v]


def expand_create_security_groups(d):
    v = d.get("security_group")
    if not v:
        return None

    return [{"id": v}]


def build_update_parameters(opts):
    # all params can be updated except on vpc_id
    update_opts = build_create_parameters(opts)
    if update_opts.has_key("vpc_id"):
        update_opts.pop("vpc_id")

    return update_opts


def send_create_request(module, params, client):
    # the endpoint: https://as-api.xxx.com/autoscaling-api/v1/{{project_id}}
    url = "scaling_group"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_group): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_update_request(module, params, client):
    # the endpoint: https://as-api.xxx.com/autoscaling-api/v1/{{project_id}}
    url = build_path(module, "scaling_group/{id}")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_group): error running api(update), "
               "url: %s%s, params:%s, error: %s" % (client.endpoint, url, params, str(ex)))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "scaling_group/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_group): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "scaling_group/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hcs_as_group): error running api(read), "
               "url: %s%s, error: %s" % (client.endpoint, url, str(ex)))
        module.fail_json(msg=msg)

    return navigate_value(r, ["scaling_group"], None)


def send_list_request(module, client, url):
    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hcs_as_group): error running api(list), "
               "url: %s%s, error: %s" % (client.endpoint, url, str(ex)))
        module.fail_json(msg=msg)

    return navigate_value(r, ["scaling_groups"], None)


def fill_read_resp_body(body):
    """
    build resource from response body
    :param body: response body from List or Read
    :return: resource object in read response format
    """

    return {
        "scaling_group_id": body.get("scaling_group_id"),
        "scaling_group_status": body.get("scaling_group_status"),
        "scaling_group_name": body.get("scaling_group_name"),
        "scaling_configuration_id": body.get("scaling_configuration_id"),
        "desire_instance_number": body.get("desire_instance_number"),
        "min_instance_number": body.get("min_instance_number"),
        "max_instance_number": body.get("max_instance_number"),
        "cool_down_time": body.get("cool_down_time"),
        "health_periodic_audit_time": body.get("health_periodic_audit_time"),
        "available_zones": body.get("available_zones"),
        "vpc_id": body.get("vpc_id"),
        "networks": body.get("networks"),
        "security_groups": body.get("security_groups"),
        "instance_terminate_policy": body.get("instance_terminate_policy"),
        "delete_publicip": body.get("delete_publicip"),
    }


def build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["group_name"])
    if v or v in [False, 0]:
        query_params.append(
            "scaling_group_name=" + (str(v) if v else str(v).lower()))

    v = navigate_value(opts, ["configuration_id"])
    if v or v in [False, 0]:
        query_params.append(
            "scaling_configuration_id=" + (str(v) if v else str(v).lower()))

    query_link = "?limit=10&start_number={start_number}"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


if __name__ == '__main__':
    main()
