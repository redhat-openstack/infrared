import yaml
import bugzilla


class IRWorkaroundFactory(object):
    """
    Factory class for IRWorkaround instances
    """
    def __new__(cls, data, username=None, password=None):
        """
        Return an instance of a class based on bug type
        :param data: Dictionary contains the data of a workaround
        :param username: Server authentication username
        :param password: Server authentication password
        :return:
        """
        if data['type'] == 'bugzilla':
            return IRBugzillaWorkaround(data, username, password)
        raise NotImplemented('Unsupported type: {}'.format(data['type']))


class IRWorkaround(object):
    """
    Base class for InfraRed workarounds
    """
    def __init__(self, data):
        """
        Class initializer
        :param data: Dictionary contains the data of a workaround
        """
        self._data = data

    @property
    def status(self):
        """
        Abstract method to return bug status
        """
        import inspect
        raise NotImplementedError('"{}" method not implemented {}'.format(
            inspect.currentframe().f_code.co_name, self.__class__))

    @property
    def data(self):
        """
        Returns the workaround data
        """
        return self._data

    @staticmethod
    def dump(data, stream):
        """
        Serialize a Python object into a YAML stream.
        :param data: Sequence contains data on workarounds
        :param stream: Stream object in 'write' mode
        """
        yaml.safe_dump(data, stream, default_flow_style=False)

    @staticmethod
    def get_workarounds_by_status(workarounds, statuses):
        """
        Returns a list of workarounds with the desired statuses
        :param workarounds: A sequence contains IRWorkaround objects
        :param statuses: A sequence contains statuses, only workarounds with
        status in this sequence will be returned
        """
        return [workaround.data for workaround in workarounds if
                workaround.status in statuses]


class IRBugzillaWorkaround(IRWorkaround):
    """
    InfraRed class for Bugzilla workarounds
    """
    def __init__(self, data, username, password):
        """
        Class initializer
        :param data: Dictionary contains the workaround data
        :param username: Server authentication username
        :param password: Server authentication password
        """
        super(self.__class__, self).__init__(data)
        self.username = username
        self.password = password
        self.bzapi = bugzilla.Bugzilla(self.data['base_url'])

        if self.username and self.password:
            self.bzapi.login(user=self.username, password=self.password)

    @property
    def status(self):
        """
        Return's the status ob the workaround's bug
        """
        return self.bzapi.getbug(self.data['id']).status
