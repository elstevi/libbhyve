import pytest
from libbhyve.disk import Disk

# Default test parameters
DEFAULT_DRIVER="ahci-hd"
DEFAULT_PATH="/var/log/messages"

def test_disk_path():
    # This should work
    assert Disk(DEFAULT_PATH, DEFAULT_DRIVER)
    
    # This should not
    with pytest.raises(TypeError, match="Disk does not exist"):
        assert Disk('/foo/bar/d', DEFAULT_DRIVER)

def test_disk_driver():
    # This should work
    assert Disk(DEFAULT_PATH, 'ahci-hd')
    assert Disk(DEFAULT_PATH, 'virtio-blk')
    
    with pytest.raises(TypeError, match="Invalid driver"):
        assert Disk(DEFAULT_PATH, 'foobar')

@pytest.fixture()
def test_disk():
    yield Disk(DEFAULT_PATH, DEFAULT_DRIVER)

def test_disk_dump(test_disk):
    d = test_disk.dump()
    if not d['path'] or not d['driver']:
        assert "Incomplete object dump"

def test_disk_start(test_disk):
    i = 0
    assert test_disk.start(i)

def test_disk_stop(test_disk):
    assert test_disk.stop()

def test_disk_print(test_disk):
    assert isinstance(test_disk.__repr__(), str)
