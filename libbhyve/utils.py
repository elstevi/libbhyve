import subprocess

from re import match
from subprocess import check_output

def shell(command, simple_return=False):
    """ Execute a command on the host system """
    process = subprocess.Popen(command, shell=True)
    return process

def log(level, message):
    entry = '[%s] %s' % (level, message)
    print(entry)
    return entry

def nginx_reload():
    subprocess.check_output("/usr/sbin/service nginx reload", shell=True)

def bridge_exists(name):
    output = check_output('ifconfig -g bridge'.encode('ascii'), shell=True).decode('utf-8')
    if match('^{}\n$'.format(name), output):
        return True
    else:
        return False
