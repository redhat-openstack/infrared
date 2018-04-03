'''
  Infrared-compose up - read infrared-compose.yaml file and execute all
states. Create object for each and execute and store state into file and
'''

import argparse
import yaml

from jinja2 import Template
from prettytable import PrettyTable
from stack import Stack

class Compose(object):


    def __init__(self, opts):
        self.compose_cfg = self.render_compose(opts.file)
        self.stack = self.compose_cfg.get('stack', {})
        self.nodaemon = opts.nodaemon
        self.name = opts.name

    def render_compose(self, yaml_file):
        with open(yaml_file) as fd:
            template = Template(fd.read())
            conf = template.render()
        return yaml.safe_load(conf)

    def up(self):
        for stack_name, stack_args in self.stack.iteritems():
            if self.name not in (stack_name, 'all'):
                continue

            with Stack(stack_name, stack_args) as stack:
                stack.execute()

    def inspect(self):
        Stack.inspect(self.name)

    def log(self):
        Stack.log(self.name)

    def rm(self):
        names = [name for name in self.stack.iterkeys()
            if self.name in (name, 'all')]

        for name in names:
            Stack(name).remove_state()

    def list(self):
        table = PrettyTable(['Id', 'Name', 'Status', 'Date'])

        names = [name for name in self.stack.iterkeys()
            if self.name in (name, 'all')]

        for name in names:
            state = Stack(name).load_state()
            if 'stack' not in state.keys():
                continue
            st = state['stack']
            table.add_row([
                st['Id'],
                st['Name'],
                st['Status'],
                st['Date']])

        print(table)


def cli():
    parser = argparse.ArgumentParser(description='infrared compose tool')
    parser.add_argument('cmd', help='Deploy infrared plugins')
    parser.add_argument('--file', '-f', help='Infrared compose file',
        default='infrared-compose.yaml')
    parser.add_argument('--nodaemon', help='Execute infrared as daemon',
        default=False, action='store_true')
    parser.add_argument('--name', help='Name',
        default='all')
    return parser.parse_args()


def main():
    '''ir-compose up --name stack_name'''

    args = cli()
    comp = Compose(args)
    if hasattr(comp, args.cmd):
        r = getattr(comp, args.cmd)()
