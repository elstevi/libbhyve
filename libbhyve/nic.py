from custom_t import NIC_TYPES
from re import match
from subprocess import check_output
from utils import shell

class Nic():
    def __init__(self, bridge, driver, mac='auto'):
        # Validate that the driver is valid
        if driver not in NIC_TYPES:
            raise TypeError('Invalid driver %s' % driver)

        # Make sure that the mac address is valid
        if type(mac) is not str:
            raise TypeError('Mac should be a string but was %s %s' % (type(mac), mac))
        if not match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()) and not mac == 'auto':
            raise TypeError('Invalid mac addr %s' % mac)

        # Make sure that the bridge is valid
#        if type(bridge) is not str:
#            raise TypeError('Bridge should be a string')

        if not bridge in check_output("ifconfig -g bridge", shell=True):
            raise TypeError('Bridge %s does not exist' % bridge)

        # Set all internal object variables
        self.mac    = mac.lower()
        self.bridge = bridge
        self.driver = driver
        self.tap = 'none'

    def create(self):
        print("Network create waves hello and does nothing")

    def delete(self):
        print("Network delete waves hello and does nothing")

    def dump(self):
        rtrn = {}
        for v in vars(self):
            rtrn[v] = vars(self)[v]
        return rtrn

    def start(self, i):
        if 'auto' not in self.mac:
            mac_str = ',mac=%s' % self.mac
        else:
            mac_str = ""

        self.tap = check_output("ifconfig tap create | tr -d '\n'", shell=True)
        shell('ifconfig %s addm %s' % (self.bridge, self.tap))
        return '-s %s,%s,%s%s ' % (i, self.driver, self.tap, mac_str)

    def stop(self):
        shell('ifconfig %s deletem %s' % (self.bridge, self.tap))
        shell('ifconfig %s destroy' % self.tap)

    def __repr__(self):
        conndisc = 'Disconnected'
        if self.tap is not None:
            conndisc = 'Connected'
        return '<virtual %s nic attached to %s mac: %s, %s>' % (self.driver, self.bridge, self.mac, conndisc)

