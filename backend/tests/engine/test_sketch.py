import pytest

from app.common.sketch import (
    IDENTIFIER_COLUMNS,
    K_DEFAULT,
    containment,
    h64,
    jaccard,
    make_sketch,
    normalize,
)

KEY = b"mini-test-key"


@pytest.mark.parametrize(
    "column,raw,expected",
    [
        ("email", " Ravi.Menon@Example.com ", "ravi.menon@example.com"),
        ("phone", "+91-9876543221", "9876543221"),
        ("phone", "98765 43221", "9876543221"),
        ("phone", "09876543221", "9876543221"),
        ("policy_no", " nh-2025-004217 ", "NH-2025-004217"),
        ("full_name", "  RAVI   menon ", "ravi menon"),
    ],
)
def test_normalization_vectors(column, raw, expected):
    assert normalize(column, raw) == expected


def test_normalize_edge_cases():
    assert normalize("email", None) == ""
    assert normalize("phone", "12345") == "12345"  # fewer than 10 digits kept whole
    assert normalize("customer_id", " C000001 ") == "C000001"
    assert normalize("city", " Raipur ") == "Raipur"  # unknown column: strip only


def test_identifier_columns_and_k():
    assert IDENTIFIER_COLUMNS == ["customer_id", "email", "phone", "policy_no"]
    assert K_DEFAULT == 512


def test_h64_is_64_bit_and_keyed():
    assert 0 <= h64(KEY, "x") < 2**64
    assert h64(KEY, "x") == h64(KEY, "x")
    assert h64(KEY, "x") != h64(b"other-key", "x")


def test_sketch_shape_sorted_hex_and_distinct():
    values = [f"C{i:06d}" for i in range(1, 1001)] + [None, "", "  "]
    sk = make_sketch("customer_id", values, KEY)
    assert sk["k"] == 512
    assert sk["distinct"] == 1000  # empties never count
    assert len(sk["hashes"]) == 512
    assert sk["hashes"] == sorted(sk["hashes"])
    assert all(len(h) == 16 and h == h.lower() and int(h, 16) >= 0 for h in sk["hashes"])


def test_small_set_sketch_is_exact():
    sk = make_sketch("customer_id", [f"C{i}" for i in range(10)], KEY)
    assert sk["distinct"] == 10 and len(sk["hashes"]) == 10


def test_jaccard_identical_and_disjoint():
    a = make_sketch("customer_id", [f"C{i}" for i in range(2000)], KEY)
    b = make_sketch("customer_id", [f"D{i}" for i in range(2000)], KEY)
    assert jaccard(a["hashes"], a["hashes"]) == 1.0
    assert jaccard(a["hashes"], b["hashes"]) == 0.0
    assert jaccard([], []) == 0.0


def test_containment_of_half_subset_near_one():
    full = [f"C{i:06d}" for i in range(1, 2001)]
    half = full[::2]  # 1000 of 2000 values
    leak = make_sketch("customer_id", half, KEY)
    export = make_sketch("customer_id", full, KEY)
    assert abs(containment(leak, export) - 1.0) <= 0.05


def test_containment_exact_for_small_sets():
    leak = make_sketch("customer_id", [f"C{i}" for i in range(10)], KEY)
    export = make_sketch("customer_id", [f"C{i}" for i in range(20)], KEY)
    assert containment(leak, export) == pytest.approx(1.0)
    # leak half inside, half outside the export
    leak2 = make_sketch("customer_id", [f"C{i}" for i in range(10, 30)], KEY)
    assert containment(leak2, export) == pytest.approx(0.5)


def test_containment_empty_leak_is_zero():
    empty = make_sketch("customer_id", [], KEY)
    export = make_sketch("customer_id", ["C1"], KEY)
    assert containment(empty, export) == 0.0


def test_determinism():
    values = [f"u{i}@mini.test" for i in range(700)]
    assert make_sketch("email", values, KEY) == make_sketch("email", list(values), KEY)
    assert make_sketch("email", values, KEY) == make_sketch("email", values[::-1], KEY)
