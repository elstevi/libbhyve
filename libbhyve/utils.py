import subprocess

def shell(command, simple_return=False):
    """ Execute a command on the host system """
    process = subprocess.Popen(command, shell=True)
    return process
def log(level, message):
    entry = '[%s] %s' % (level, message)
    print entry
    return entry
