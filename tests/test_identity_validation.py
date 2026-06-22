import pytest

from app.services.identity_service import ValidationError, validate_external_id, validate_full_name


@pytest.mark.parametrize("external_id", ["emp-0042", "a", "A1_b2-C3", "x" * 32])
def test_valid_external_ids_pass(external_id):
    validate_external_id(external_id)


@pytest.mark.parametrize(
    "external_id",
    ["", "has space", "has/slash", "../../etc/passwd", "x" * 33, "semi;colon", None],
)
def test_invalid_external_ids_raise(external_id):
    with pytest.raises(ValidationError):
        validate_external_id(external_id)


def test_valid_full_name_passes():
    validate_full_name("Jane Doe")


def test_empty_full_name_raises():
    with pytest.raises(ValidationError):
        validate_full_name("   ")


def test_overlong_full_name_raises():
    with pytest.raises(ValidationError):
        validate_full_name("x" * 200)
