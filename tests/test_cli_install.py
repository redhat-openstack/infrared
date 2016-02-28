import os

import pytest


@pytest.mark.parametrize('args, output', [
    ("ospd --version 7.3",
     {"build": "Y3", "version": "7"}),
    ("ospd --version 7 --build latest",
     {"build": "latest", "version": "7"}),
    ("ospd --version 7 --build Y3",
     {"build": "Y3", "version": "7"}),
    ("ospd --version 7 --build 2016-01-26.1",
     {"build": "2016-01-26.1", "version": "7"}),
    ("ospd --version 8 --build 2016-01-26.1 --core-version 7",
     {"build": "2016-01-26.1",
      "version": "8",
      "core": {
          "version": "7",
          "build": "latest"}}),
    ("ospd --version 8 --core-version 7",
     {"build": "latest",
      "version": "8",
      "core": {
          "version": "7",
          "build": "latest"}}),
    ("ospd --version 8 --core-build 2016-01-26.1",
     {"build": "latest",
      "version": "8",
      "core": {
          "version": "8",
          "build": "2016-01-26.1"}}),
])
def test_product_repo(args, output):
    from cli import install

    args = install.get_args(args=args.split(" "))
    product = install.set_product_repo(args)
    assert output == product["installer"]["product"]


@pytest.mark.parametrize('args, output', [
    ("",
     {"protocol": "ipv4",
      "backend": "vxlan",
      "isolation": {
          "enable": "no"},
      "ssl": "no"}),
    ("--network-protocol ipv6 --network-isolation yes --network-variant sriov --ssl yes",
     {"protocol": "ipv6",
      "backend": "sriov",
      "isolation": {
          "enable": "yes",
          "type": "three-nics-vlans",
          'file': "environments/net-three-nic-with-vlans.yaml"},
      "ssl": "yes"}),
])
def test_set_network_details(args, output):
    from cli import install

    args = "ospd --version 7 " + args
    args = args.strip(" ")
    args = install.get_args(args=args.split(" "))
    network = install.set_network_details(args)
    assert output == network["installer"]["overcloud"]["network"]


def test_set_network_template():
    from cli import install

    filename = "ipv4.yml"
    def_path = os.path.join(install.get_settings_dir(),
                            install.ENTRY_POINT,
                            "ospd", "network",
                            "templates")
    act_filename = install.set_network_template(filename,
                                                def_path)
    assert act_filename == os.path.join(def_path, filename)

    from cli import exceptions
    with pytest.raises(exceptions.IRFileNotFoundException):
        install.set_network_template("bad/file/path", def_path)

    from tests.test_cwd import utils
    alt_file = os.path.join(utils.TESTS_CWD, "placeholder_overwriter.yml")
    new_act_filename = install.set_network_template(alt_file, def_path)
    assert alt_file == new_act_filename


@pytest.mark.parametrize('args, output', [
    ("--version 7 --image-server www.fake_url.to/images",
     {"server": "www.fake_url.to/images",
      "files": {"discovery": "discovery-ramdisk.tar",
                "deployment": "deploy-ramdisk-ironic.tar",
                "overcloud": "overcloud-full.tar"}}),
    ("--version 20 --image-server www.fake_url.to/images",
     {"server": "www.fake_url.to/images",
      "files": {"discovery": "ironic-python-agent.tar",
                "overcloud": "overcloud-full.tar"}})
])
def test_set_image(args, output):
    from cli import install

    args = "ospd " + args
    args = install.get_args(args=args.split(" "))
    images = install.set_image(args)
    assert images["installer"]["overcloud"]["images"] == output

def test_set_image_build():
    from cli import exceptions
    from cli import install

    args = "ospd --version 7"
    args = install.get_args(args=args.split(" "))
    with pytest.raises(exceptions.IRNotImplemented):
        install.set_image(args)
