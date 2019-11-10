from libbhyve.config import *
from libbhyve.disk import Disk
from jinja2 import Environment, PackageLoader
from libbhyve.nic import Nic
from os.path import isfile
from time import sleep
from libbhyve.utils import log, shell
import subprocess
import json
import os
import uuid

class VM:
    """ This function initializes a virtual machine object.

    Passing no arguments returns a blank virtual machine template. From there, you can just alter the class attributes of the class

    args:
        infile (str, opt): contains the path of a virtual machine json file to load
        indict (str, opt): contains a dictionary of values to load from
    """
    def __init__(self, infile=None, indict={}):
        self.auto_start = False
        self.bootrom = '/usr/local/share/uefi-firmware/BHYVE_UEFI.fd'
        # Possible options: stdio, nmdm_auto
        self.com1 = 'nmdm_auto'
        self.com2 = None
        self.disk = []
        self.fbuf_wait = False
        self.iso = None
        self.memory = 256
        self.name = ''
        self.ncpus = 1
        self.network = []
        self.uuid = None

        if infile:
            if not isfile(infile):
                raise TypeError('infile is not a file')
            else:
                self.load_from_file('%s' % (infile))
        elif indict:
            if not isinstance(indict, dict):
                raise TypeError('indict is not a dict!')
            else:
                self.load_from_dict(something)

        if self.uuid == None:
            self.uuid = str(uuid.uuid4())

    def is_tap_bridge_member(self, tap, bridge):
        """ Determine if a bridge and tap are joined
            args:
                tap (str): name of tap device
                bridge (str): name of bridge device

            returns:
                true or false
        """
        cmd = "ifconfig %s | grep ': %s ' || true" % (bridge, tap)
        output = subprocess.check_output(cmd, shell=True)
        if output != None and output.count('\n') == 1:
            return True
        else:
            return False


    def load_from_file(self, fpath):
        """ Convenience function to open json configuration file

            args:
                fpath (str): path to vm configuration file.
        """
        with open(fpath) as f:
            fconf = json.loads(f.read())
        self.load_from_dict(fconf)


    def load_from_dict(self, d):
        """ Deserialize VM object from dict

        args:
            d (dict): target dictionary to deserialize
        """

        self.disk = []
        self.network = []
        for key, value in d.items():
            if key == 'network':
                for v in value:
                    self.network.append(
                        Nic(
                            str(v['bridge']),
                            str(v['driver']),
                            mac=str(v['mac']),
                        )
                    )
            elif key == 'disk':
                for v in value:
                    self.disk.append(
                        Disk(
                            path=v.get('path'),
                            driver=v.get('driver'),
                            create_disk=v.get('create_disk'),
                            backing=v.get('backing'),
                            size=v.get('size'),
                        )
                    )
            else:
                setattr(self, key, value)


    def dump_to_file(self, path):
        with open(path, 'w+') as f:
            json.dump(self.dump_to_dict(), f)


    def dump_to_dict(self):
        """ Deserialize object to dictionary:

            returns:
                serialized dictionary
        """
        rtrn = {}
        for key in vars(self):
            if key == 'disk' or key == 'network':
                rtrn[key] = []
                rtrn['vnc_port'] = self.get_vnc_port()
                for item in vars(self)[key]:
                    try:
                        rtrn[key].append(item.dump())
                        print('dump %s' % item)
                    except Exception as e:
                        with open('/tmp/libbhyve.log', 'w+') as f:
                            f.write('%s %s %s' % (e, type(item), item))
            else:
                rtrn[key] = getattr(self, key)
        return rtrn

    def create(self):
        """ Trigger the create hook in the subclasses
        """
        for disk in self.disk:
            disk.create()
        for network in self.network:
            network.create()

    def __repr__(self):
        ret = "< VM: %s" % self.name
        for v in vars(self):
            ret += "  <%s: %s>" % (v, vars(self)[v])
            ret += ">"
        return ret

    def start(self):
        """ Start the virtual machine object on this hypervisor
        """
        # todo: this function should be cleaned up, maybe? Should the arguments be added to a list?
        pcistr = ''
        lpcistr = ''
        # Start with 1, because the hostbridge is 0
        i=1

        # Add all of the nics
        for nic in self.network:
            pcistr += ' %s' % nic.start(i)
            i = i + 1

        # Add all of the disks
        for disk in self.disk:
            pcistr += ' %s' % disk.start(i)
            i = i + 1


        if len(self.iso) != 0:
            pcistr += '-s %s,ahci-cd,%s' % (i, self.iso)
            i = i + 1

        if self.fbuf_wait == True:
            fbw = ',wait'
        else:
            fbw = ''
        pcistr += ' -s %s,fbuf,tcp=127.0.0.1:5900%s' % (i, fbw)
        i = i + 1

        # PCI Bridge devices
        for port in ['com1', 'com2']:
            value = getattr(self, port)
            if value is not None:
                lpcistr += '-l %s,%s ' % (port, self.render_com_device(value))

        if self.bootrom is not None:
            lpcistr += '-l bootrom,%s' % self.bootrom

        bhyve_cmd = "/usr/sbin/bhyve -c {ncpus} -m {memory}M -A -H -w -s 0,hostbridge -s 31,lpc {pcistr} {lpcistr} {name} >> /tmp/vm_{name} 2>&1".format(
            pcistr=pcistr,
            lpcistr=lpcistr,
            **self.__dict__
        )
        p = subprocess.Popen(bhyve_cmd, shell=True)
        #self.insert_websockify_config()

    def render_com_device(self, device):
        if device == 'stdio':
            return device
        elif 'nmdm' in device:
            return '/dev/nmdm_{}_A'.format(self.name)
        else:
            assert TypeError('Unvalid value for com port {}'.format(device))

    def get_pid(self):
        """ Get the pid of this virtual machine on this hypervisor

            returns:
                int(pid)
                or
                0 if not running
        """
        try:
            pid = subprocess.check_output('ps auxww | grep -v grep | grep "bhyve: %s" | awk \'{print $2}\'' % self.name, shell=True)
            return int(pid)
        except ValueError:
            return 0

    def get_vnc_port(self):
        """ I have a patch to bhyve that allows a virtual machine to chose a random port by passing 0 to the socket command. This then checks what port
        it got based on the process table.

        returns:
            int(port)
            or
            0 if not found
        """
        # todo: this should return None if it cannot be determined, not 0

        try:
            # todo: this should use the enum
            if self.status() != 'Running':
                raise ValueError('VM is not running, no vnc port available')
            else:
                port = subprocess.check_output("sockstat | grep %i | grep '\*:\*' | awk '{print $6}' | cut -d \: -f2" % self.get_pid(), shell=True)
                return int(port)
        except ValueError:
            return 0

    def block_until_poweroff(self, timeout):
        """ Hold execution captive until vm powers off or timeout is met.

        args:
            timeout(int): how long to wait until we give up
        """
        # todo: timeout should be optional and we should block forever

        i = 0
        while i < timeout:
            if self.get_pid() != 0:
                i = i + 1
                sleep(1)
            else:
                return True
        return False

    def stop(self):
        """ Stop a virtual machine """
        # todo: low timeout is just for testing
        #TIMEOUT = 120
        TIMEOUT = 12
        # todo: perhaps the os module has a way we can do this without shelling out
        subprocess.call('kill %s' % self.get_pid(), shell=True)
        log('info', 'Signaling vm %s to shut down' % self.name)
        if not self.block_until_poweroff(TIMEOUT):
            subprocess.call('kill -9 %s' % self.get_pid(), shell=True)
            log('info', 'Timeout (%s seconds) reached, killing vm %s' % (TIMEOUT, self.name))
        else:
            log('info', 'VM %s turned off gracefully' % self.name)
        subprocess.call('bhyvectl --vm=%s --destroy' % self.name, shell=True)
        sleep(2) # Give process a chance to die
        if self.get_pid() != 0:
            raise OSError("VM did not die when it was supposed to")
        for network in self.network:
            network.stop()
        for disk in self.disk:
            disk.stop()
        #self.remove_websockify_config()

    def status(self):
        """ Get the status of a virtual machine

            returns:
                'Stopped' or 'Running'
        """

        # todo should this return an enum?
        if self.get_pid() == 0:
            return 'Stopped'
        else:
            return 'Running'

    def restart(self):
        """ Stop VM if running, start it back up """
        if self.status() == 'Running':
            self.stop()
        self.start()

    def delete(self):
        """ Stops and deletes virtual machine configuration, disk, network. """
        if self.status() == 'Running':
            self.stop()
        for disk in self.disk:
            disk.delete()
        for network in self.network:
            network.delete()
        os.remove('%s/%s' % (VM_DIR, self.name))

