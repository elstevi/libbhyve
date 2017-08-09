import pytest
from libbhyve.nic import Nic
from libbhyve.utils import shell
# Set some default parameters
DEFAULT_BRIDGE="bridge10001"
DEFAULT_DRIVER="virtio-net"

# Test libbhyve/nic
@pytest.fixture()
def test_bridge():
    br = DEFAULT_BRIDGE
    shell("ifconfig %s create" % br)
    yield br
    shell("ifconfig %s destroy" % br)

@pytest.fixture()
def test_nic(test_bridge):
    yield Nic(test_bridge, DEFAULT_DRIVER)

def test_nic_mac(test_bridge):
    """ Test passing different mac values to the NIC object"""

    # Good mac address
    assert Nic(test_bridge, DEFAULT_DRIVER, mac="00:00:00:00:00:01")
    assert Nic(test_bridge, DEFAULT_DRIVER, mac="auto")

    # Bad mac address
    with pytest.raises(TypeError, match="Mac should be a string"):
        assert Nic(test_bridge, DEFAULT_DRIVER, mac=None)
 
    with pytest.raises(TypeError, match="Invalid mac addr"):
        assert Nic(test_bridge, DEFAULT_DRIVER, mac="00:00:00:00:00:0")

    with pytest.raises(TypeError, match="Invalid mac addr"):
        assert Nic(test_bridge, DEFAULT_DRIVER, mac=":::::")

    with pytest.raises(TypeError, match="Invalid mac addr"):
        assert Nic(test_bridge, DEFAULT_DRIVER, mac="cow")

def test_nic_driver(test_bridge):
    # Valid drivers:
    assert Nic(test_bridge, "virtio-net")
    assert Nic(test_bridge, "e1000")

    # Invalid drivers
    with pytest.raises(TypeError, match="Invalid driver"):
        assert Nic(test_bridge, "beef")

    with pytest.raises(TypeError, match="Invalid driver"):
        assert Nic(test_bridge, None)


def test_invalid_bridge():

    # Try with a bridge that doesn't exist
    ne_br='nonexistent_bridge'
    with pytest.raises(TypeError, match="Bridge %s does not exist" % ne_br):
        assert Nic(ne_br, DEFAULT_DRIVER)

    # Try with a non-string bridge object
    with pytest.raises(TypeError, match="Bridge should be a string"):
        assert Nic(None, DEFAULT_DRIVER)

def test_nic_dump(test_nic):
    d = test_nic.dump()
    if not d['bridge'] or not d['mac'] or not d['driver'] or not d['tap']:
        assert "Invalid nic dump"

def test_nic_start_stop(test_nic):
    i = 0
    test_nic.start(i)
    test_nic.mac = "00:00:00:00:00:01"
    test_nic.start(i)
    test_nic.stop()

def test_repr_nic(test_nic):
    print test_nic
