from datetime import datetime

try:
    from ansible.plugins.callback import CallbackBase
    ANSIBLE2 = True
except ImportError:
    ANSIBLE2 = False


class CallbackModule(CallbackBase if ANSIBLE2 else object):
    __color = '\033[01;30m'
    __endcolor = '\033[00m'

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)

        # capture datetime.now for __del__, as otherwise
        # it may be destroyed before this instance is
        self.__dtnow = datetime.now

        self.__debug_time = {
            'playbook': None,
            'play': None,
            'task': None,
            'total': datetime.now()
        }

    def __del__(self):
        self.__nexttime('task')
        self.__nexttime('play')
        self.__nexttime('playbook')
        self.__nexttime('total')

    def __nexttime(self, which):
        old = self.__debug_time[which]
        now = self.__dtnow()
        self.__debug_time[which] = now

        if old is not None:
            diff = now - old
            diff_t = now - self.__debug_time['total']

            if 'play' != 'total':
                which = 'previous ' + which
            msg = '[[ {0} time: {1} = {2:.2f}s / {3:.2f}s ]]'.format(
                which, diff, diff.total_seconds(), diff_t.total_seconds())

            print('%s%s%s' % (self.__color,
                              msg.rjust(79, ' '),
                              self.__endcolor))

    def playbook_on_start(self):
        self.__nexttime('playbook')

    def playbook_on_play_start(self, pattern):
        self.__nexttime('play')

    def playbook_on_task_start(self, name, is_conditional):
        self.__nexttime('task')

    # def runner_on_failed(self, host, res, ignore_errors=False):
    #     self.__stoptime('task')

    # def runner_on_ok(self, host, res):
    #     self.__stoptime('task')

    # def runner_on_error(self, host, msg):
    #     self.__stoptime('task')

    # def runner_on_skipped(self, host, item=None):
    #     self.__stoptime('task')

    # def runner_on_unreachable(self, host, res):
    #     self.__stoptime('task')

    # def runner_on_no_hosts(self):
    #     self.__stoptime('task')
