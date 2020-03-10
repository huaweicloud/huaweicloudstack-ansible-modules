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
module: hcs_as_configuration
description:
    - auto-scaling configuration management.
short_description: Creates a resource of auto-scaling configuration in Huawei Cloud Stack
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
    configuration_name:
        description:
            - Specifies the name of the AS configuration. Value requirements consists of 1 to 64
              characters, including letters, digits, underscores(_), and hyphens(-).
        type: str
        required: true
    instance_id:
        description:
            - Specifies the ID of ECS instance. When using the existing instance specifications
              as the template to create AS configurations, specify this argument.
              In this case, flavor_id, image_id, and disks arguments do not take effect.
              If the instance_id argument is not specified, flavor_id, image_id, and disks arguments are mandatory.
        type: str
        required: false
    flavor_id:
        description:
            - Specifies the ID of the system flavor.
        type: str
        required: false
    image_id:
        description:
            - Specifies the ID of the system image.
        type: str
        required: false
    disks:
        description:
            - Specifies the configuration of the ECS's disks.
        type: list
        required: false
        suboptions:
            disk_type:
                description:
                    - Specifies whether the disk is a system disk or a data disk.
                type: str
                choices: ['SYS', 'DATA']
                required: true
            volume_type:
                description:
                    - Specifies the ECS disk type.
                    - SATA is common I/O disk type.
                    - SAS is high I/O disk type.
                    - SSD is ultra-high I/O disk type.
                    - other types defined in CCS.
                type: str
                required: true
            size:
                description:
                    - Specifies the system disk size, in GB. The system disk size must be
                      greater than or equal to the minimum system disk size supported
                      by the image (min_disk attribute of the image).
                type: int
                required: true
    ssh_key_name:
        description:
            - Specifies the name of the SSH key used for logging in to the ECS.
        type: str
        required: false
    admin_pass:
        description:
            - Specifies the initial login password of the administrator account
              for logging in to an ECS using password authentication. The Linux
              administrator is root, and the Windows administrator is
              Administrator. Password complexity requirements, consists of 8 to
              26 characters. The password must contain at least three of the
              following character types 'uppercase letters, lowercase letters,
              digits, and special characters (!@$%^-_=+[{}]:,./?)'. The password
              cannot contain the username or the username in reverse. The
              Windows ECS password cannot contain the username, the username in
              reverse, or more than two consecutive characters in the username.
        type: str
        required: false
    user_data:
        description:
            - Specifies the user data to be injected during the ECS creation
              process. Text, text files, and gzip files can be injected.
              The content to be injected must be encoded with base64.
              The maximum size of the content to be injected (before encoding)
              is 32 KB. For Linux ECSs, this parameter does not take
              effect when adminPass is used.
        type: str
        required: false
    server_metadata:
        description:
            - Specifies the metadata of ECS to be created.
        type: dict
        required: false
    public_ip:
        description:
            - Specifies the elastic IP address of the instance.
        type: dict
        required: false
        suboptions:
            type:
                description:
                    - Specifies the EIP type.
                type: str
                required: true
            bandwidth:
                description:
                    - Specifies the dedicated bandwidth object.
                type: dict
                required: false
                suboptions:
                    charge_mode:
                        description:
                            - Specifies whether the bandwidth is billed by traffic or by bandwidth size. 
                        type: str
                        choices: ['bandwidth', 'traffic']
                        required: true
                    share:
                        description:
                            - Specifies the bandwidth sharing type. The system only supports PER (indicates exclusive bandwidth).
                        type: str
                        required: true
                    size:
                        description:
                            - Specifies the bandwidth size. The value ranges from 1
                              Mbit/s to 2000 Mbit/s by default. The specific range may
                              vary depending on the configuration in each region. You
                              can see the bandwidth range of each region on the
                              management console.
                        type: int
                        required: true
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create an auto-scaling configuration
- name: create a vpc
  hcs_as_configuration:
    configuration_name: "ansible_as_configuration_test"
    flavor_id: "0c324e05-f9d6-431c-8010-a33fcd4708e9"
    image_id: "ccb858d6-1aa8-433c-8cc3-4500a56cee2f"
    disks:
      - size: 40
        volume_type: "SATA"
        disk_type: "SYS"
    ssh_key_name: "ansible_key"
'''

RETURN = '''
    id:
        description:
            - Specifies the ID of the AS configuration.
        type: str
        returned: success
'''

from ansible.module_utils.hwc_utils import (
    Config, HwcClientException, HwcModule, are_different_dicts, build_path,
    get_region, is_empty_value, navigate_value, wait_to_finish)


def build_module():
    return HwcModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'],
                       type='str'),
            configuration_name=dict(type='str', required=True),
            instance_id=dict(type='str'),
            flavor_id=dict(type='str'),
            image_id=dict(type='str'),
            disks=dict(type='list', elements='dict', options=dict(
                disk_type=dict(type='str', required=True, choices=['SYS', 'DATA']),
                volume_type=dict(type='str', required=True),
                size=dict(type='int', required=True),
            )),
            ssh_key_name=dict(type='str'),
            admin_pass=dict(type='str'),
            user_data=dict(type='str'),
            server_metadata=dict(type='dict'),
            public_ip=dict(type='dict', options=dict(
                type=dict(type='str', required=True),
                bandwidth=dict(type='dict', options=dict(
                    charge_mode=dict(type='str', required=True, choices=['bandwidth', 'traffic']),
                    share=dict(type='str', required=True),
                    size=dict(type='int', required=True)
                )),
            )),
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
            # read as configuration resource by id
            resource = read_resource(config)
        else:
            # search as configuration resource by name
            v = search_resource(config)
            n = len(v)
            if n > 1:
                raise Exception("Found more than one resource(%s)" % ", ".join([
                    navigate_value(i, ["id"])
                    for i in v
                ]))

            if n == 1:
                module.params['id'] = navigate_value(v[0], ["id"])
                resource = v[0]

        changed = False
        result = dict()
        if module.params['state'] == 'present':
            if not resource:
                if not module.check_mode:
                    result['action'] = 'create'
                    create(config)
                changed = True
            else:
                obj = build_identity_object(module)
                if are_different_dicts(obj, resource):
                    raise Exception(
                        "Cannot change option for an existing auto-scaling configuration(%s)."
                        % module.params.get('id'))
        else:
            if resource:
                if not module.check_mode:
                    result['action'] = 'delete'
                    delete(config)
                changed = True

    except Exception as ex:
        module.fail_json(msg=str(ex))

    else:
        result['changed'] = changed
        result['id'] = module.params['id']
        module.exit_json(**result)


def build_identity_object(module):
    return {
        "id": module.params.get("id"),
        "configuration_name": module.params.get("configuration_name"),
        "instance_id": module.params.get("instance_id"),
        "flavor_id": module.params.get("flavor_id"),
        "image_id": module.params.get("image_id"),
        "disks": module.params.get("disks"),
        "public_ip": module.params.get("public_ip"),
        "ssh_key_name": module.params.get("ssh_key_name"),
        "admin_pass": module.params.get("admin_pass"),
        "user_data": module.params.get("user_data"),
        "server_metadata": module.params.get("server_metadata"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    params = build_create_parameters(module.params)
    r = send_create_request(module, params, client)
    module.params['id'] = navigate_value(r, ["scaling_configuration_id"])


def delete(config):
    module = config.module
    client = config.client(get_region(module), "autoscaling", "project")

    r = send_delete_request(module, None, client)


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
    link = "scaling_configuration" + query_link

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
    instance_config = dict()

    v = navigate_value(opts, ["configuration_name"], None)
    if not is_empty_value(v):
        params["scaling_configuration_name"] = v

    v = navigate_value(opts, ["instance_id"], None)
    if not is_empty_value(v):
        instance_config["instance_id"] = v

    v = navigate_value(opts, ["flavor_id"], None)
    if not is_empty_value(v):
        instance_config["flavorRef"] = v

    v = navigate_value(opts, ["image_id"], None)
    if not is_empty_value(v):
        instance_config["imageRef"] = v

    v = expand_create_disks_param(opts, None)
    if not is_empty_value(v):
        instance_config["disk"] = v

    v = navigate_value(opts, ["ssh_key_name"], None)
    if not is_empty_value(v):
        instance_config["key_name"] = v

    v = navigate_value(opts, ["admin_pass"], None)
    if not is_empty_value(v):
        instance_config["adminPass"] = v

    v = navigate_value(opts, ["user_data"], None)
    if not is_empty_value(v):
        instance_config["user_data"] = v

    v = navigate_value(opts, ["server_metadata"], None)
    if not is_empty_value(v):
        instance_config["metadata"] = v

    v = expand_create_publicip(opts, None)
    if not is_empty_value(v):
        instance_config["public_ip"] = v

    if instance_config:
        params["instance_config"] = instance_config

    if not params:
        return None

    return params


def expand_create_disks_param(d, array_index):
    disks = []
    new_ai = dict()
    if array_index:
        new_ai.update(array_index)

    v = navigate_value(d, ["disks"], new_ai)
    if not v:
        return disks

    n = len(v)
    for i in range(n):
        new_ai["disks"] = i
        transformed = dict()

        v = navigate_value(d, ["disks", "disk_type"], new_ai)
        if not is_empty_value(v):
            transformed["disk_type"] = v

        v = navigate_value(d, ["disks", "volume_type"], new_ai)
        if not is_empty_value(v):
            transformed["volume_type"] = v

        v = navigate_value(d, ["disks", "size"], new_ai)
        if not is_empty_value(v):
            transformed["size"] = v

        if transformed:
            disks.append(transformed)

    return disks


def expand_create_publicip(d, array_index):
    r = dict()

    v = expand_create_publicip_bandwidth(d)
    if not is_empty_value(v):
        r["bandwidth"] = v

    v = navigate_value(d, ["public_ip", "type"], array_index)
    if not is_empty_value(v):
        r["ip_type"] = v

    if not r:
        return None

    return {"eip": r}


def expand_create_publicip_bandwidth(d):
    bandwidth = dict()

    raw = navigate_value(d, ["public_ip", "bandwidth"])
    if is_empty_value(raw):
        return bandwidth

    v = navigate_value(raw, ["charge_mode"])
    if not is_empty_value(v):
        bandwidth["charge_mode"] = v

    v = navigate_value(raw, ["share"])
    if not is_empty_value(v):
        bandwidth["share"] = v

    v = navigate_value(raw, ["size"])
    if not is_empty_value(v):
        bandwidth["size"] = v

    return bandwidth


def send_create_request(module, params, client):
    # the endpoint: https://as-api.xxx.com/autoscaling-api/v1/{{project_id}}
    url = "scaling_configuration"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_configuration): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "scaling_configuration/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hcs_as_configuration): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "scaling_configuration/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hcs_as_configuration): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["scaling_configuration"], None)


def send_list_request(module, client, url):
    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hcs_as_configuration): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["scaling_configurations"], None)


def fill_read_resp_body(body):
    """build resource from response body"""

    result = dict()

    result["id"] = body.get("scaling_configuration_id")
    result["configuration_name"] = body.get("scaling_configuration_name")

    config_body = body.get("instance_config")
    if not config_body:
        raise Exception("instance_config is missing in response body")

    result["instance_id"] = config_body.get("instance_id")
    result["flavor_id"] = config_body.get("flavorRef")
    result["image_id"] = config_body.get("imageRef")
    result["ssh_key_name"] = config_body.get("key_name")
    result["admin_pass"] = config_body.get("adminPass")
    result["user_data"] = config_body.get("user_data")
    result["server_metadata"] = config_body.get("metadata")
    result["public_ip"] = config_body.get("public_ip")

    v = fill_read_resp_disks(config_body.get("disk"))
    result["disks"] = v

    return result


def fill_read_resp_disks(value):
    if not value:
        return None

    disks = []
    for item in value:
        disk = {
            "disk_type": item.get("disk_type"),
            "volume_type": item.get("volume_type"),
            "size": item.get("size"),
        }
        disks.append(disk)

    return disks


def build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["configuration_name"])
    if v or v in [False, 0]:
        query_params.append(
            "scaling_configuration_name=" + (str(v) if v else str(v).lower()))

    v = navigate_value(opts, ["image_id"])
    if v or v in [False, 0]:
        query_params.append(
            "image_id=" + (str(v) if v else str(v).lower()))

    query_link = "?limit=10&start_number={start_number}"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


if __name__ == '__main__':
    main()
