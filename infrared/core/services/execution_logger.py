import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


class ExecutionLoggerManager(object):
    """Logger to log all the ir commands with all the parameters. """

    FILE_ARGUMENTS = ['--from-file']

    def __init__(self,
                 ansible_config_path,
                 log_name="ir-commands",
                 log_file='ir-commands.log',
                 log_level=logging.INFO):
        self.log = logging.getLogger(log_name)
        is_log_present = os.path.isfile(log_file)
        self.log.addHandler(RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=1))
        self.log.setLevel(log_level)

        # add extra line if log file is new
        if not is_log_present:
            self.log.info(
                "# infrared setup instruction: "
                "http://infrared.readthedocs.io/en/latest/bootstrap.html"
                "#setup\n")

            self.log_file(ansible_config_path)

    def command(self):
        """Saves current ir command with arguments to the log. """

        self.log.info("# executed at %s", datetime.now())

        # ensure we see the content of the answers file
        for file_option in self.FILE_ARGUMENTS:
            if file_option in sys.argv:
                file_index = sys.argv.index(file_option)
                if file_index and len(sys.argv) >= file_index + 2:
                    self.log_file(sys.argv[file_index + 1])

        self.log.info("infrared %s", " ".join(sys.argv[1:]).replace(
            ' -', ' \\\n    -'))
        self.log.info("")

    def log_file(self, file_name):
        """Logs the file to be used with the infrared. """

        if os.path.isfile(file_name):
            file_dir = os.path.dirname(file_name)
            if file_dir:
                self.log.info("mkdir -p %s", file_dir)
            with open(file_name) as conf_file:
                self.log.info(
                    "# create file\n"
                    "cat << EOF > %s\n"
                    "%s"
                    "\nEOF\n", file_name, conf_file.read())
