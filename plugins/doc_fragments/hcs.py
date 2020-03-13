# Copyright: (c) 2018, Huawei Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # HCS doc fragment.
    DOCUMENTATION = '''
options:
    auth:
        description:
            - Dictionary containing auth information as needed by the cloud's auth plugin strategy.
        type: dict
        suboptions:
            auth_url:
                description:
                    - The Identity authentication URL.
                type: str
                required: true
            username:
                description:
                    - The user name to login with.
                type: str
                required: true
            password:
                description:
                    - The password to login with.
                type: str
                required: true
            domain_name:
                description:
                    - The name of the Domain to scope to. (currently only domain names are supported,
                      and not domain IDs).
                type: str
                required: true
            project_name:
                description:
                    - The name of the Project. (currently only project names are supported,
                      and not project IDs).
                type: str
                required: true
    region:
        description:
            - The region to which the project belongs.
        type: str
    id:
        description:
            - The id of resource to be managed.
        type: str
notes:
  - For authentication, you can set auth/auth_url using the C(OS_AUTH_URL) env variable.
  - For authentication, you can set auth/username using the C(OS_USERNAME) env variable.
  - For authentication, you can set auth/password using the C(OS_PASSWORD) env variable.
  - For authentication, you can set auth/domain_name using the C(OS_DOMAIN_NAME) env variable.
  - For authentication, you can set auth/project_name using the C(OS_PROJECT_NAME) env variable.
  - For authentication, you can set region using the C(OS_REGION_NAME) env variable.
  - Environment variables values will only be used if the playbook values are not set.
'''

