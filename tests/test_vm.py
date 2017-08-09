import pytest
from libbhyve.vm import VM
from os.path import abspath
from time import sleep
from subprocess import CalledProcessError
from libbhyve.utils import shell

@pytest.fixture()
def test_freebsd_vm():
    fp = abspath('tests/freebsd.conf')
    vm = VM(fp)
    vm.save()
    yield vm
    if vm.status() == "Stopped":
        vm.start()
    vm.delete()

#@pytest.fixture()
#def test_vm_running(test_freebsd_vm, monkeypatch):
   # assert test_freebsd_vm.status() == "Stopped", "VM is running before we started it!"
   # test_freebsd_vm.start()
   # assert test_freebsd_vm.status() == "Running", "VM is not running right after start!"

  #  yield test_freebsd_vm

  #  test_freebsd_vm.stop()


#    # We want to catch the VM
#    def mockfalse():
#        return 111
#    test_freebsd_vm.start()
#    monkeypatch.setattr(test_freebsd_vm, 'get_pid', mockfalse)
#    with pytest.raises(OSError, match="VM did not die when it was supposed to"):
#        test_freebsd_vm.stop()
#    monkeypatch.undo()

# we don't support fbuf wait yet!
#def test_vm_fbuf_wait(test_freebsd_vm):
#    if test_freebsd_vm.status() == "Running":
#        test_freebsd_vm.stop()
#    test_freebsd_vm.fbuf_wait=True
#    test_freebsd_vm.start()
#    test_freebsd_vm.stop()
#    test_freebsd_vm.fbuf_wait=False


def test_bad_vm():
    with pytest.raises(OSError, match="does not exist"):
        myvm = VM('blahalsdjf')

def test_is_tap_bridge_member(test_freebsd_vm):
    assert test_freebsd_vm.is_tap_bridge_member('tap10000', 'bridge10000') == False
    shell('ifconfig bridge10000 create')
    assert test_freebsd_vm.is_tap_bridge_member('tap10000', 'bridge10000') == False
    shell('ifconfig tap10000 create')
    shell('ifconfig bridge10000 addm tap10000')
    assert test_freebsd_vm.is_tap_bridge_member('tap10000', 'bridge10000') == True
    shell('ifconfig tap10000 destroy')
    shell('ifconfig bridge10000 destroy')

def test_vm_get_pid(test_freebsd_vm):
    if test_freebsd_vm.status() == "Stopped":
        test_freebsd_vm.start()
    assert test_freebsd_vm.get_pid() != 0, "VM returned 0 pid, but we started it"
    test_freebsd_vm.stop()
    assert test_freebsd_vm.get_pid() == 0, "VM didn't return 0 pid, but we stopped it"

def test_vm_from_file():
    fp = abspath('tests/freebsd.conf')
    junkvm = VM(fp)
    junkvm.name = 'junk'
    junkvm.save()
    junkvm = VM('junk')
    junkvm.delete()

def test_vm_power(test_freebsd_vm):
    if test_freebsd_vm.status() == "Stopped":
        test_freebsd_vm.start()
    test_freebsd_vm.restart()
    test_freebsd_vm.stop()

def test_vm_stop_non_graceful_fail(monkeypatch):
    # We want to catch the VM
    fp = abspath('tests/freebsd.conf')
    test_freebsd_vm = VM(fp)
    if test_freebsd_vm.status() == "Stopped":
        test_freebsd_vm.start()
    def mockfalse():
        return 111
    monkeypatch.setattr(test_freebsd_vm, 'get_pid', mockfalse)
    with pytest.raises(OSError, match="VM did not die when it was supposed to"):
        test_freebsd_vm.stop()
    monkeypatch.undo()

def test_vm_repr(test_freebsd_vm):
    print test_freebsd_vm
