==========
Shade Role
==========

This role creates Shade virtualenv, which can be used for Ansible os_* modules

Default path for the virtualenv is /var/tmp/venv_shade. You can overwrite it with "shade_path_venv", example::

    ---
    roles:
      - role: shade
        shade_path_venv: /var/tmp/new_shade_location
