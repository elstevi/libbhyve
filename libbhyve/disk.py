from custom_t import DISK_TYPES
from os.path import isfile
from os import stat

class Disk():
    def __init__(self, path, driver):
        if driver not in DISK_TYPES:
            raise TypeError('Invalid driver %s' % driver)
        if not isfile(path):
            try:
                stat(path)
            except OSError:
                raise TypeError('Disk does not exist %s' % path)
        self.path = path
        self.driver = driver

    def dump(self):
        rtrn = {}
        for v in vars(self):
            rtrn[v] = vars(self)[v]
        return rtrn

    def start(self, i):
        return '-s %s,%s,%s ' % (i, self.driver, self.path)

    def stop(self):
        return True

    def __repr__(self):
        return '<virtual %s disk attached to %s>' % (self.driver, self.path)
