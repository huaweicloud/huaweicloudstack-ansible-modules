#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Huawei
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: hcs_lb_member
short_description: Add/Delete a member for a pool in load balancer from Huawei Cloud Stack
version_added: "1.0"
author: "Huawei Inc. (@huaweicloud)"
requirements: ["openstacksdk"]
description:
   - Add or Remove a member for a pool from Huawei Cloud Stack.
options:
   name:
     description:
        - Name that has to be given to the member
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   pool:
     description:
        - The name or id of the pool that this member belongs to.
     required: true
   protocol_port:
     description:
        - The protocol port number for the member.
     default: 80
   subnet:
     description:
        - The name or id of the subnet that the member service is accessible from.
          This argument is mandatory when I(state) is 'present'.
   address:
     description:
        - The IP address of the member. This argument is mandatory when I(state) is 'present'.
extends_documentation_fragment: openstack
'''

RETURN = '''
id:
    description: The member UUID.
    returned: On success when I(state) is 'present'
    type: str
    sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
member:
    description: Dictionary describing the member.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Unique UUID.
            type: str
            sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
        name:
            description: Name given to the member.
            type: str
            sample: "test"
        description:
            description: The member description.
            type: str
            sample: "description"
        is_admin_state_up:
            description: The administrative state of the member.
            type: bool
            sample: true
        protocol_port:
            description: The protocol port number for the member.
            type: int
            sample: 80
        subnet_id:
            description: The subnet ID that the member service is accessible from.
            type: str
            sample: "489247fa-9c25-11e8-9679-00224d6b7bc1"
        address:
            description: The IP address of the backend member server.
            type: str
            sample: "192.168.2.10"
'''

EXAMPLES = '''
# Create a member
- hcs_lb_member:
    state: present
    name: test-member
    pool: test-pool
    subnet: test-subnet
    address: 192.168.10.3
    protocol_port: 8080

# Delete a listener
- hcs_lb_member:
    state: absent
    name: test-member
    pool: test-pool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, \
    openstack_module_kwargs, openstack_cloud_from_module


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(type='str', required=True),
        state=dict(default='present', choices=['absent', 'present']),
        pool=dict(type='str', required=True),
        protocol_port=dict(type='int', default=80),
        subnet=dict(type='str'),
        address=dict(type='str'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)
    sdk, cloud = openstack_cloud_from_module(module)

    name = module.params['name']
    pool = module.params['pool']
    subnet = module.params['subnet']
    address = module.params['address']

    try:
        changed = False

        pool_ret = cloud.network.find_pool(name_or_id=pool)
        if not pool_ret:
            module.fail_json(msg='pool %s is not found' % pool)

        pool_id = pool_ret.id
        member = cloud.network.find_pool_member(name, pool_id)

        if module.params['state'] == 'present':
            if not member:
                if not subnet or not address:
                    module.fail_json(
                        msg='subnet and address are mandatory when state is present'
                    )

                subnet_ret = cloud.get_subnet(subnet)
                if not subnet_ret:
                    module.fail_json(
                        msg='subnet %s is not found' % subnet
                    )
                subnet_id = subnet_ret.id

                member = cloud.network.create_pool_member(
                    pool_ret,
                    name=name,
                    subnet_id=subnet_id,
                    address=address,
                    protocol_port=module.params['protocol_port']
                )
                changed = True

            module.exit_json(changed=changed, member=member.to_dict(),
                             id=member.id)

        elif module.params['state'] == 'absent':
            if member:
                cloud.network.delete_pool_member(member, pool_ret)
                changed = True

            module.exit_json(changed=changed)
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == "__main__":
    main()
