import subprocess
from libbhyve.custom_t import DISK_TYPES
from os.path import exists, isfile
from os import remove, stat

class Disk():
    def __init__(self, path=None, driver='ahci-hd', create_disk=False, backing="zvol", size='10G'):
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
            if self.backing == "zvol" and not exists('/dev/zvol/%s' % self.path):
                subprocess.check_output("zfs create -p -V %s %s" % (self.size, self.path), shell=True)

            elif self.backing == "file" and not exists(self.path):
                subprocess.check_output("truncate -s %s %s" % (self.size, self.path), shell=True)
            self.path = '%s' % self.path

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
