"""The no-network fixture (lean-test-suite P-4, TC-4): a socket connect fails outside tests/e2e/."""

import socket
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

CONFTEST = Path(__file__).parents[1] / "conftest.py"
CONNECT = "import socket\n\ndef test_connect():\n    socket.create_connection(('localhost', 1), timeout=1)\n"


def test_a_unit_test_cannot_open_a_socket():
    with pytest.raises(RuntimeError, match="network access is not allowed outside tests/e2e/"):
        socket.create_connection(("localhost", 1))


def test_an_e2e_test_may_open_a_socket(pytester):
    """Run the real conftest over a copy of the tier layout: e2e reaches the network, unit does not."""
    pytester.makeconftest(CONFTEST.read_text())
    pytester.mkdir("e2e").joinpath("test_e2e.py").write_text(CONNECT)
    pytester.mkdir("unit").joinpath("test_unit.py").write_text(CONNECT)
    result = pytester.runpytest_subprocess("-p", "no:cacheprovider")  # in-process would inherit this test's own patch
    result.assert_outcomes(failed=2)
    output = result.stdout.str()
    assert output.count("ConnectionRefusedError") >= 1  # the e2e test got a real refused connection
    assert output.count("network access is not allowed outside tests/e2e/") >= 1  # the unit test got the rule
