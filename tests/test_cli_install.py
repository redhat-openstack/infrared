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
    import os
    from cli import install

    spec_file = open(os.path.join(install.TMP_SETTINGS_DIR, "ospd", "ospd.spec"))
    args = install.get_args(spec=spec_file, args=args.split(" "))
    product = install.set_product_repo(args)
    assert output == product["product"]
