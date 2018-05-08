import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def get_image_path(ansible_var):
    base_image_path = ansible_var['base_image_path']
    image_name = ansible_var['url'].split('/')[-1]
    return os.path.join(base_image_path, image_name)

def test_image_exists(host):
    '''
        Check image has been downloaded and has appropriate user/group.
    '''
    var = host.ansible.get_variables()
    f = host.file(get_image_path(var))

    assert f.exists
    assert f.user == 'qemu'
    assert f.group == 'qemu'

def test_uploaded_authorize_file(host):
    '''
        Check that uploaded file exists in image.
    '''
    var = host.ansible.get_variables()
    image_path = get_image_path(var)
    authorize_file = '/root/.ssh/authorized_keys'
    pattern = 'Mock data'

    read_authorize_file = host.run(
        'export LIBGUESTFS_BACKEND=direct; virt-cat -a {0} {1}'.format(
                image_path, authorize_file))

    assert read_authorize_file.stdout.find(pattern) >= 0

def test_removed_dhclient_file(host):
    '''
        Check that dhclient.conf file was removed from image.
    '''
    var = host.ansible.get_variables()
    image_path = get_image_path(var)
    dhclient_file = '/etc/dhcp/dhclient.conf'

    check_dhclient_file = host.run(
        'export LIBGUESTFS_BACKEND=direct; virt-ls -a {0} {1}'.format(
                image_path, os.path.dirname(dhclient_file)))

    assert dhclient_file not in check_dhclient_file.stdout
