# encoding: utf-8


def _colored_emitter(emit):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if levelno >= 50:
            color = '\x1b[31m'  # red
        elif levelno >= 40:
            color = '\x1b[31m'  # red
        elif levelno >= 30:
            color = '\x1b[33m'  # yellow
        elif levelno >= 20:
            color = '\x1b[32m'  # green
        elif levelno >= 10:
            color = '\x1b[36m'  # purple
        else:
            color = '\x1b[0m'   # normal

        args[1].msg = color + str(args[1].msg) + '\x1b[0m'  # normal
        return emit(*args)
    return new


def enable():
    """
    enables colored logging
    """
    from logging import StreamHandler
    StreamHandler.emit = _colored_emitter(StreamHandler.emit)
