from playrandom.playrandom import main as playrandom
import sys, os
import pytest

def test_help():
    # check if the -h flag correctly exits
    with pytest.raises(SystemExit):
        sys.argv.append('-h')
        playrandom();

