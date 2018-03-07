import subprocess
from custom_t import DISK_TYPES
from os.path import isfile
from os import remove, stat

class Disk():
    def __init__(self, path=None, driver=None, create_disk=False, backing="zvol", size=False):
        if driver not in DISK_TYPES:
            raise TypeError('Invalid driver %s' % driver)
#        if not isfile(path):
#            try:
#                stat(path)
#            except OSError:
#                raise TypeError('Disk does not exist %s' % path)
        self.path = path
        self.driver = driver
        self.create_disk = create_disk
        self.backing = backing
        self.size = size
    def create(self):
        if self.create_disk == "yes":
            if self.backing == "zvol":
                subprocess.check_output("zfs create -V %s %s" % (self.size, self.path), shell=True)

            elif self.backing == "file":
                subprocess.check_output("truncate -s %s %s" % (self.size, self.path), shell=True)
            self.path = '/dev/zvol/%s' % self.path

    def delete(self):
        if self.create_disk == "yes":
            if self.backing == "zvol":
                subprocess.check_output("zfs destroy -R %s" % (self.path), shell=True)

            elif self.backing == "file":
                remove('%s' % self.path)

    def dump(self):
        rtrn = {}
        for v in vars(self):
            rtrn[v] = vars(self)[v]
        return rtrn

    def start(self, i):
        if self.backing == 'zvol':
            return '-s %s,%s,/dev/zvol/%s ' % (i, self.driver, self.path)
        elif self.backing == 'file':
            return '-s %s,%s,%s ' % (i, self.driver, self.path)

    def stop(self):
        return True

    def __repr__(self):
        return '<virtual %s disk attached to %s, backing %s>' % (self.driver, self.path, self.backing)
