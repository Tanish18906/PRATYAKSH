import pytest

from app.privacy.mask import mask_row, mask_value


@pytest.mark.parametrize(
    "column,raw,expected",
    [  # contract section 10 examples
        ("email", "ravi.menon@example.com", "r***@example.com"),
        ("phone", "+91-9876543221", "+91-98******21"),
        ("full_name", "Ravi Menon", "R. M."),
        ("policy_no", "NH-2025-004217", "NH**********17"),
        ("customer_id", "C0048211", "*****211"),
        ("dob", "1990-05-14", "1990-**-**"),
        ("city", "Raipur", "***"),  # any other personal column
    ],
)
def test_contract_vectors(column, raw, expected):
    assert mask_value(column, raw) == expected


def test_masked_value_length_is_preserved_for_partial_masks():
    for col, raw in [("phone", "+91-9876543221"), ("policy_no", "NH-2025-004217"), ("customer_id", "C0048211")]:
        assert len(mask_value(col, raw)) == len(raw)


@pytest.mark.parametrize(
    "column,raw,expected",
    [  # shorter than (or equal to) the kept parts: mask everything
        ("phone", "12345", "*****"),
        ("phone", "12345678", "********"),
        ("policy_no", "AB12", "****"),
        ("customer_id", "C12", "***"),
    ],
)
def test_short_values_are_fully_masked(column, raw, expected):
    assert mask_value(column, raw) == expected


def test_email_edge_cases():
    assert mask_value("email", "a@b.co") == "a***@b.co"
    assert mask_value("email", "no-at-sign") == "***"
    assert mask_value("email", "@example.com") == "***@example.com"


def test_name_and_dob_edge_cases():
    assert mask_value("full_name", "  ravi   kumar menon ") == "R. K. M."
    assert mask_value("full_name", "Madonna") == "M."
    assert mask_value("dob", "14/05/1990") == "***"  # not an ISO date: do not guess a year


def test_none_and_empty():
    assert mask_value("email", None) == ""
    assert mask_value("phone", "") == ""


def test_mask_row_masks_every_field_and_never_leaks():
    row = {"full_name": "Ravi Menon", "phone": "+91-9876543221", "policy_no": "NH-2025-004217",
           "created_at": "2026-10-08T22:00:00Z"}
    out = mask_row(row)
    assert out == {"full_name": "R. M.", "phone": "+91-98******21", "policy_no": "NH**********17",
                   "created_at": "***"}
    assert "Ravi" not in str(out) and "9876543221" not in str(out)
