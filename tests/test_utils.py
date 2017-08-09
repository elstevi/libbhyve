import pytest
from libbhyve.utils import log

def test_log():
    assert log('crit', 'world') == "[crit] world"
