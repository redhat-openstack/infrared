#!/usr/bin/env python
from cli.app import CONF, IRFactory


def main_provision():
    app = IRFactory.create("provisioner", CONF)
    if app:
        app.run()


def main_install():
    app = IRFactory.create("installer", CONF)
    if app:
        app.run()


if __name__ == '__main__':
    main_provision()
    main_install()
