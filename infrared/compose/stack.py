from datetime import datetime
import os
import json
import shutil
import sys

from infrared.main import main as infrared
from infrared.core.utils import logger
#from infrared.core.services import CoreSettings

LOG = logger.LOG
STACK_DIR = '{path}/.compose/{name}'
STACK_STATE_FILE = 'state.json'

class Stack(object):

    def __init__(self, stack_name, stack_args=[]):
        self.stack_name = stack_name
        self.stack_args = stack_args

        # CoreSettings class doesn't expose infarared_home attribute
        # settings = CoreSettings()
        # infarared_home = settings.infarared_home
        infarared_home = os.path.abspath(os.environ.get(
            "IR_HOME", os.getcwd()))
        self.stack_state = STACK_DIR.format(
            path=infarared_home, name=stack_name)
        self.state_file = os.path.join(
            self.stack_state, STACK_STATE_FILE)
        self.prepare_env()

    def prepare_env(self):
        if not os.path.isdir(self.stack_state):
            os.makedirs(self.stack_state)

    def execute(self):
        for plugin in self.stack_args:
            opts = ''
            for plugin_name,plugin_opts in plugin.iteritems():
                opts += plugin_name
                for k,v in plugin_opts.iteritems():
                    if isinstance(v, list):
                        for (_k,_v) in zip([k] * len(v), v):
                            opts += ' --{0} {1}'.format(_k, _v)
                        break
                    opts += ' --{0} {1}'.format(k, v)
            rc = infrared(opts.split())
            if rc != 0:
                LOG.error('Plugin {0} execution is failed'.format(
                    plugin_name))
                sys.exit(rc)

    def log(self, name):
        with open(self.log_file) as fd:
            while True:
                for line in fd.readlines():
                    print(line.decode('string-escape'))

    def save_state(self):
        state_structure = {
            'stack': {
                'Id': 'ID',
                'Name': self.stack_name,
                'Status': 'Deployed',
                'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Args': self.stack_args
            }
        }

        with open(self.state_file, 'w') as fd:
            fd.write(json.dumps(state_structure))

    def load_state(self):
        state = {}

        if os.path.isfile(self.state_file):
            with open(self.state_file) as fd:
                state = json.load(fd)

        return state

    def remove_state(self):
        if os.path.isdir(self.stack_state):
            shutil.rmtree(self.stack_state)
