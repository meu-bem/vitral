import pytest

from vitral.data_loader import load_national_rules


@pytest.fixture(scope="session")
def br_rules():
    return load_national_rules()
