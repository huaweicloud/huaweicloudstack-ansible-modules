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
module: hcs_as_policy
description:
    - auto-scaling policy management.
short_description: Creates a resource of auto-scaling policy in Huawei Cloud Stack
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
    group_id:
        description:
            - Specifies the AS group ID.
        type: str
        required: true
    policy_name:
        description:
            - Specifies the name of the AS policy. Value requirements consists of 1 to 64
              characters, including letters, digits, underscores(_), and hyphens(-).
        type: str
        required: true
    policy_type:
        description:
            - Specifies the type of the AS policy.
        type: str
        required: true
        choices: ['ALARM', 'SCHEDULED', 'RECURRENCE']
    alarm_id:
        description:
            - Specifies The alarm rule ID. This argument is mandatory when policy_type is set to 'ALARM'.
        type: str
        required: false
    scheduled_policy:
        description:
            - Specifies the periodic or scheduled AS policy.
              This argument is mandatory when scaling_policy_type is set to 'SCHEDULED' or 'RECURRENCE'.
        type: dict
        required: false
        suboptions:
            launch_time:
                description:
                    - Specifies the time when the scaling action is triggered.
                      If policy_type is set to 'SCHEDULED', the time format is YYYY-MM-DDThh:mmZ.
                      If policy_type is set to 'RECURRENCE', the time format is hh:mm..
                type: str
                required: true
            recurrence_type:
                description:
                    - Specifies the periodic triggering type.
                      This argument is mandatory when policy_type is set to 'RECURRENCE'.
                type: str
                choices: ['Daily', 'Weekly', 'Monthly']
            recurrence_value:
                description:
                    - Specifies the frequency at which scaling actions are triggered.
                type: str
            start_time:
                description:
                    - Specifies the start time of the scaling action triggered periodically.
                      The time format complies with UTC. The current time is used by default.
                      The time format is YYYY-MM-DDThh:mmZ.
                type: str
            end_time:
                description:
                    - Specifies the end time of the scaling action triggered periodically.
                      This argument is mandatory when policy_type is set to 'RECURRENCE'.
                      The time format complies with UTC. The time format is YYYY-MM-DDThh:mmZ.
                type: str
    policy_action:
        description:
            - Specifies the action of the AS policy.
        type: dict
        required: false
        suboptions:
            operation:
                description:
                    - Specifies the operation to be performed.
                type: str
                choices: ['ADD', 'REMOVE', 'SET']
                default: 'ADD'
            instance_number:
                description:
                    - Specifies the number of instances to be operated.
                type: int
                default: 1
    cool_down_time:
        description:
            - Specifies the cooling duration (in seconds). The value ranges from 0 to 86400.
        type: int
        default: 900
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
  register: group
# create an auto-scaling policy
- name: create an auto-scaling policy
  hcs_as_policy:
    group_id: "{{ group.id }}"
    policy_name: "ansbile_as_policy_test"
    policy_type: "RECURRENCE"
    cool_down_time: 600
    scheduled_policy:
      launch_time: "00:00"
      recurrence_type: "Weekly"
      recurrence_value: "1,3,5"
      end_time: "2020-06-30T00:00Z"
    policy_action:
      operation: "ADD"
      instance_number: 1
'''

RETURN = '''
    id:
        description:
            - Specifies the ID of the AS policy.
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
            group_id=dict(type='str', required=True),
            policy_name=dict(type='str', required=True),
            policy_type=dict(type='str', required=True, choices=['ALARM', 'SCHEDULED', 'RECURRENCE']),
            alarm_id=dict(type='str'),
            scheduled_policy=dict(type='dict', options=dict(
                launch_time=dict(type='str', required=True),
                recurrence_type=dict(type='str', choices=['Daily', 'Weekly', 'Monthly']),
                recurrence_value=dict(type='str'),
                start_time=dict(type='str'),
                end_time=dict(type='str'),
            )),
            policy_action=dict(type='dict', options=dict(
                operation=dict(type='str', choices=['ADD', 'REMOVE', 'SET']),
                instance_number=dict(type='int', default=1),
            )),
            cool_down_time=dict(type='int'),
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
            # read as policy resource by id
            resource = read_resource(config)
        else:
            # search as policy resource by name
            v = search_resource(config)
            n = len(v)
            if n > 1:
                raise Exception("Found more than one resource(%s)" % ", ".join([
                    navigate_value(i, ["scaling_policy_id"])
                    for i in v
                ]))

            if n == 1:
                module.params['id'] = navigate_value(v[0], ["scaling_policy_id"])
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

    return {
        "scaling_group_id": module.params.get("group_id"),
        "scaling_policy_id": module.params.get("id"),
        "scaling_policy_name": module.params.get("policy_name"),
        "scaling_policy_type": module.params.get("policy_type"),
        "scaling_policy_action": module.params.get("policy_action"),
        "alarm_id": module.params.get("alarm_id"),
        "scheduled_policy": module.params.get("scheduled_policy"),
        "cool_down_time": module.params.get("cool_down_time"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    params = build_create_parameters(module.params)
    r = send_create_request(module, params, client)
    module.params['id'] = navigate_value(r, ["scaling_policy_id"])


def update(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    params = build_update_parameters(module.params)
    r = send_update_request(module, params, client)
    module.params['id'] = navigate_value(r, ["scaling_policy_id"])


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
    path = build_path(module, "scaling_policy/{group_id}/list")
    query_link = build_query_link(module.params)
    link = path + query_link

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


def expand_scheduled_policy_opts(d):
    opts = d.get("scheduled_policy")
    if not opts:
        return None

    params = dict()

    v = navigate_value(opts, ["launch_time"])
    if not is_empty_value(v):
        params["launch_time"] = v

    v = navigate_value(opts, ["recurrence_type"])
    if not is_empty_value(v):
        params["recurrence_type"] = v

    v = navigate_value(opts, ["recurrence_value"])
    if not is_empty_value(v):
        params["recurrence_value"] = v

    v = navigate_value(opts, ["start_time"])
    if not is_empty_value(v):
        params["start_time"] = v

    v = navigate_value(opts, ["end_time"])
    if not is_empty_value(v):
        params["end_time"] = v

    return params


def expand_policy_action_opts(d):
    opts = d.get("policy_action")
    if not opts:
        return None

    params = dict()

    v = navigate_value(opts, ["operation"])
    if not is_empty_value(v):
        params["operation"] = v

    v = navigate_value(opts, ["instance_number"])
    if not is_empty_value(v):
        params["instance_number"] = v

    return params


def build_create_parameters(opts):
    """
    - change the input parameters with required name or value format of create API
    - ignore empty parameter
    """

    params = dict()

    v = navigate_value(opts, ["group_id"])
    if not is_empty_value(v):
        params["scaling_group_id"] = v

    v = navigate_value(opts, ["policy_name"])
    if not is_empty_value(v):
        params["scaling_policy_name"] = v

    v = navigate_value(opts, ["policy_type"])
    if not is_empty_value(v):
        params["scaling_policy_type"] = v

    v = navigate_value(opts, ["alarm_id"])
    if not is_empty_value(v):
        params["alarm_id"] = v

    v = expand_scheduled_policy_opts(opts)
    if not is_empty_value(v):
        params["scheduled_policy"] = v

    v = expand_policy_action_opts(opts)
    if not is_empty_value(v):
        params["scaling_policy_action"] = v

    v = navigate_value(opts, ["cool_down_time"])
    if not is_empty_value(v):
        params["cool_down_time"] = v

    return params


def build_update_parameters(opts):
    # all params can be updated except on group_id
    update_opts = build_create_parameters(opts)
    if update_opts.has_key("scaling_group_id"):
        update_opts.pop("scaling_group_id")

    return update_opts


def send_create_request(module, params, client):
    # the endpoint: https://as-api.xxx.com/autoscaling-api/v1/{{project_id}}
    url = "scaling_policy"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_policy): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_update_request(module, params, client):
    # the endpoint: https://as-api.xxx.com/autoscaling-api/v1/{{project_id}}
    url = build_path(module, "scaling_policy/{id}")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_policy): error running api(update), "
               "url: %s%s, params:%s, error: %s" % (client.endpoint, url, params, str(ex)))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "scaling_policy/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_policy): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "scaling_policy/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hcs_as_policy): error running api(read), "
               "url: %s%s, error: %s" % (client.endpoint, url, str(ex)))
        module.fail_json(msg=msg)

    return navigate_value(r, ["scaling_policy"], None)


def send_list_request(module, client, url):
    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hcs_as_policy): error running api(list), "
               "url: %s%s, error: %s" % (client.endpoint, url, str(ex)))
        module.fail_json(msg=msg)

    return navigate_value(r, ["scaling_policies"], None)


def fill_read_resp_body(body):
    """
    build resource from response body
    :param body: response body from List or Read
    :return: resource object in read response format
    """
    policy_action = None
    v = body.get("scaling_policy_action")
    if v:
        policy_action = {
            "operation": v.get("operation"),
            "instance_number": v.get("instance_number")
        }

    scheduled_policy = None
    v = body.get("scheduled_policy")
    if v:
        scheduled_policy = {
            "launch_time": v.get("launch_time"),
            "recurrence_type": v.get("recurrence_type"),
            "recurrence_value": v.get("recurrence_value"),
            "start_time": v.get("start_time"),
            "end_time": v.get("end_time")
        }

    return {
        "scaling_group_id": body.get("scaling_group_id"),
        "scaling_policy_id": body.get("scaling_policy_id"),
        "scaling_policy_name": body.get("scaling_policy_name"),
        "scaling_policy_type": body.get("scaling_policy_type"),
        "alarm_id": body.get("alarm_id"),
        "cool_down_time": body.get("cool_down_time"),
        "scaling_policy_action": policy_action,
        "scheduled_policy": scheduled_policy
    }


def build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["policy_name"])
    if v or v in [False, 0]:
        query_params.append(
            "scaling_policy_name=" + (str(v) if v else str(v).lower()))

    v = navigate_value(opts, ["policy_type"])
    if v or v in [False, 0]:
        query_params.append(
            "scaling_policy_type=" + (str(v) if v else str(v).lower()))

    query_link = "?limit=10&start_number={start_number}"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


if __name__ == '__main__':
    main()
