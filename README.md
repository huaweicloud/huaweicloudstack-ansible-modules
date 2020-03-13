huaweicloud.huaweicloudstack_ansible_modules
=========

Prerequisite
------------

The usage of this ansible modules assumes that you've already setup an Ansible environment for HuaweiCloud Stack.

[Installed the ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) in your environment.

Installation
------------

1. Install the modules
  ``` bash
  $ ./install.sh
  ```
2. Install required packages
  ``` bash
  $ sudo pip install -r requirement.txt
  ```


Example Playbook
----------------
```
$ cat test.yml
- hosts: localhost
  tasks:
    - name: create an auto-scaling group
      hcs_as_group:
        auth:
          auth_url: "{{ auth_url }}"
          username: "{{ user_name }}"
          password: "{{ password }}"
          domain_name: "{{ domain_name }}"
          project_name: "{{ project_name }}"
        region: "{{ region }}"

        group_name: "{{ group_name }}"
        state: present
        vpc_id: "{{ vpc_id }}"
        networks: ["{{ test_network }}"]
        desire_instance_number: 2
        min_instance_number: 1
        max_instance_number: 5
        cool_down_time: 600
        health_periodic_audit_time: 15
        delete_publicip: True
```

Run ansible
-----------
```
$ ansible-playbook test.yml
```

License
-------
Apache 2.0
