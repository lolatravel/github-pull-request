import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_cli(runner):
    pass
