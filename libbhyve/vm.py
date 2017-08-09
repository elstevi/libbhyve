from config import *
from disk import Disk
from nic import Nic
from os.path import isfile
from time import sleep
from utils import log, shell
import subprocess
import json 
import os


class VM:
    def __init__(self, something):
        self.auto_start = False
        self.bootrom = '/usr/local/share/uefi-firmware/BHYVE_UEFI.fd'
        self.com1 = 'stdio'
        self.disk = []
        self.fbuf_ip = None
        self.fbuf_port = None
        self.fbuf_wait = False 
        self.iso = "" 
        self.memory = 1024 
        self.name = ''
        self.ncpus = 1
        self.network = []

        if isfile('%s/%s' % (VM_DIR, something)):
            self.load_from_file('%s/%s' % (VM_DIR, something))
        elif isfile('%s' % (something)):
            self.load_from_file('%s' % (something))
        else:
            raise OSError("VM %s does not exist" % something)

        # Make sure values are reasonable

#        self.associate_taps()


    def is_tap_bridge_member(self, tap, bridge):
        cmd = "ifconfig %s | grep ': %s ' || true" % (bridge, tap)
        output = subprocess.check_output(cmd, shell=True)
        if output != None and output.count('\n') == 1:
            return True
        else:
            return False

#    def get_taps_in_use(self):
#        cmd = "ifconfig | grep -B 7 'Opened by PID %s' | grep 'tap[0-9]*:' | cut -d \: -f1" % self.get_pid()
#        taps = subprocess.check_output(cmd, shell=True).splitlines()
#        return taps

#    def associate_taps(self):
#        taps = self.get_taps_in_use()
#        for interface in self.network:
#            for tap in taps:
#                if self.is_tap_bridge_member(tap, interface.bridge):
#                    interface.tap = tap

    def load_from_file(self, fpath):
        with open(fpath) as f:
            fconf = json.loads(f.read())
        self.load_from_dict(fconf)

    def load_from_dict(self, d):
        for key, value in d.iteritems():
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
                            v['path'],
                            v['driver'],
                        )
                    )
            else:
                exec("self.%s = '%s'" % (key, value))
    
    def dump_to_dict(self):
        rtrn = {}
        for key in vars(self):
            if key == 'disk' or key == 'network':
                rtrn[key] = []
                for item in vars(self)[key]:
                    rtrn[key].append(item.dump())
                    print 'dump %s' % item 
            else:
                rtrn[key] = getattr(self, key)
        return rtrn


    def save(self):
        d = self.dump_to_dict()
        with open('%s/%s' %(VM_DIR, self.name), 'w') as f:
            f.write(json.dumps(d))
        return True

    def __repr__(self):
        ret = "< VM: %s >" % self.name
        for v in vars(self):
            ret += "  <%s: %s>" % (v, vars(self)[v])
        return ret

    def start(self):
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

        if self.fbuf_ip != None and self.fbuf_port != None:
#            if self.fbuf_wait == True:
#                fbw = ',wait'
#            else:
#                fbw = ''
            fbw = ''
            pcistr += ' -s %s,fbuf,tcp=%s:%s%s' % (i, self.fbuf_ip, self.fbuf_port, fbw)
            i = i + 1

        # PCI Bridge devices
        if self.com1 is not 'None':
            lpcistr += '-l %s,%s ' % ('com1', self.com1)

        if self.bootrom is not None:
            lpcistr += '-l bootrom,%s' % self.bootrom

        bhyve_cmd = """/usr/sbin/bhyve -c %s -m %sM -A -H -w -s 0,hostbridge -s 31,lpc %s %s %s""" % (self.ncpus, self.memory, pcistr, lpcistr, self.name)
        screen_cmd = """/usr/local/bin/screen -dmS bhyve.%s sh -c '%s 2>&1 | tee /tmp/vm-%s'""" % (self.name, bhyve_cmd, self.name)
        print screen_cmd
        p = subprocess.Popen(screen_cmd, shell=True)

        socket_cmd = """/usr/local/libexec/novnc/utils/websockify/nr 0.0.0.0:%s 127.0.0.1:%s""" % ('10' + str(self.fbuf_port)[1:], self.fbuf_port)
        socket_cmd_screen = """/usr/local/bin/screen -dmS bhyve-websockify.%s %s""" % (self.name, socket_cmd)
        subprocess.check_output(socket_cmd_screen, shell=True)
        sleep(4)

    def get_pid(self):
        try:
            pid = subprocess.check_output('ps auxww | grep -v grep | grep "bhyve: %s" | awk \'{print $2}\'' % self.name, shell=True)
            return int(pid)
        except ValueError:
            return 0


    def block_until_poweroff(self, timeout):
        i = 0
        while i < timeout:
            if self.get_pid() != 0:
                i = i + 1
                sleep(1)
            else:
                return True
        return False

    def stop(self):
        # xxx fixme just for testing
        #TIMEOUT = 120
        TIMEOUT = 12
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

    def status(self):
        if self.get_pid() == 0:
            return 'Stopped'
        else:
            return 'Running'

    def restart(self):
        if self.status() == 'Running':
            self.stop()
        self.start()

    def delete(self):
        if self.status() == 'Running':
            self.stop()
        os.remove('%s/%s' % (VM_DIR, self.name))

