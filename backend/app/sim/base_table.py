"""Synthetic customer table and reusable keyed-hash cache."""

import hashlib
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from threading import Lock

import numpy as np

from .names import CITIES_BY_STATE, FIRST_NAMES, LAST_NAMES


COMPANY_SEED = 7
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
IDENTIFIERS = ("customer_id", "email", "phone", "policy_no")
STATES = ("CG", "MH", "KA", "MP", "OD", "DL", "TN", "GJ", "UP")
_CACHE_THREAD_LOCK = Lock()


def seconds(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def timestamp(value: int) -> str:
    return datetime.fromtimestamp(int(value), UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(slots=True)
class BaseTable:
    scale: str
    created: np.ndarray
    states: np.ndarray
    cities: np.ndarray
    first: np.ndarray
    last: np.ndarray
    dob: np.ndarray
    tiers: np.ndarray
    years: np.ndarray
    hashes: dict = field(default_factory=dict)

    def identifier(self, column: str, index: int) -> str:
        number = index + 1
        if column == "customer_id":
            return f"C{number:07d}"
        if column == "phone":
            return str(6_000_000_000 + (number * 7919 + 12345) % 4_000_000_000)
        if column == "policy_no":
            return f"NH-{int(self.years[index])}-{number:06d}"
        first = FIRST_NAMES[int(self.first[index])].lower()
        last = LAST_NAMES[int(self.last[index])].lower()
        return f"{first}.{last}{number}@{('example.com', 'example.org', 'example.net')[number % 3]}"

    def row(self, index: int) -> dict:
        first = FIRST_NAMES[int(self.first[index])]
        last = LAST_NAMES[int(self.last[index])]
        state = STATES[int(self.states[index])]
        return {
            "customer_id": self.identifier("customer_id", index),
            "full_name": f"{first} {last}",
            "email": self.identifier("email", index),
            "phone": self.identifier("phone", index),
            "dob": (datetime(1970, 1, 1, tzinfo=UTC) +
                    timedelta(seconds=int(self.dob[index]))).strftime("%Y-%m-%d"),
            "city": CITIES_BY_STATE[state][int(self.cities[index]) % len(CITIES_BY_STATE[state])],
            "state": state,
            "signup_date": timestamp(self.created[index])[:10],
            "created_at": timestamp(self.created[index]),
            "policy_no": self.identifier("policy_no", index),
            "premium_tier": ("basic", "silver", "gold")[int(self.tiers[index])],
        }

    def sketch(self, column: str, indices: np.ndarray) -> dict:
        values = np.unique(self.hashes[column][indices])
        return {"k": 512, "distinct": int(len(values)),
                "hashes": [f"{int(value):016x}" for value in values[:512]]}


@lru_cache(maxsize=2)
def get_base(scale: str) -> BaseTable:
    if scale not in ("demo", "bench"):
        raise ValueError("scale must be demo or bench")
    size = 310_000 if scale == "demo" else 31_000
    rng = np.random.default_rng(COMPANY_SEED)
    recent_count = round(size * 0.45)
    created = np.concatenate((
        rng.integers(seconds("2025-01-01T00:00:00Z"), seconds("2026-10-26T00:00:00Z"), recent_count),
        rng.integers(seconds("2019-01-01T00:00:00Z"), seconds("2025-01-01T00:00:00Z"), size - recent_count),
    ))
    created.sort()
    states = rng.choice(len(STATES), size=size, p=[0.35] + [0.65 / 8] * 8)
    cities = rng.integers(0, 1000, size=size, dtype=np.int16)
    first = rng.integers(0, len(FIRST_NAMES), size=size, dtype=np.int16)
    last = rng.integers(0, len(LAST_NAMES), size=size, dtype=np.int16)
    dob = rng.integers(seconds("1950-01-01T00:00:00Z"), seconds("2005-01-01T00:00:00Z"), size=size)
    tiers = rng.choice(3, size=size, p=[0.5, 0.35, 0.15])
    years = created.astype("datetime64[s]").astype("datetime64[Y]").astype(int) + 1970
    return BaseTable(scale, created, states, cities, first, last, dob, tiers, years)


def case_key(scale: str) -> bytes:
    return hashlib.sha256(f"pugmark-case-{COMPANY_SEED}-{scale}".encode()).digest()


def seeded_rng(label: str, seed: int):
    digest = hashlib.sha256(f"{label}|{seed}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


@contextmanager
def _cache_process_lock(scale: str):
    """Hold an OS lock while checking or rebuilding the shared hash cache."""
    path = CACHE_DIR / f"{scale}.lock"
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if not handle.read(1):
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            deadline = time.monotonic() + 60
            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("hash cache lock timed out")
                    time.sleep(0.05)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def warm_cache(scale: str) -> BaseTable:
    """Load or build one hash per identifier per row; public JSON never contains the key."""
    # The cache is only valid against Tanish's shared sketch implementation.
    from app.common.sketch import h64, normalize

    base = get_base(scale)
    with _CACHE_THREAD_LOCK:
        if base.hashes:
            return base
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        checksum = hashlib.sha256(base.created.tobytes() + base.states.tobytes() +
                                  base.first.tobytes() + base.last.tobytes()).hexdigest()
        expected = {"COMPANY_SEED": COMPANY_SEED, "N": len(base.created), "checksum": checksum}
        meta_path = CACHE_DIR / f"{scale}_meta.json"
        paths = {column: CACHE_DIR / f"{scale}_{column}.npy" for column in IDENTIFIERS}
        with _cache_process_lock(scale):
            try:
                meta = json.loads(meta_path.read_text())
                if meta == expected and all(path.exists() for path in paths.values()):
                    base.hashes = {column: np.load(path, mmap_mode="r")
                                   for column, path in paths.items()}
                    return base
            except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
                pass

            key = case_key(scale)
            hashes_by_column = {}
            for column, path in paths.items():
                hashes = np.fromiter(
                    (h64(key, normalize(column, base.identifier(column, index)))
                     for index in range(len(base.created))),
                    dtype=np.uint64, count=len(base.created),
                )
                np.save(path, hashes)
                hashes_by_column[column] = hashes
            temporary_meta = meta_path.with_suffix(".json.tmp")
            temporary_meta.write_text(json.dumps(expected, sort_keys=True))
            os.replace(temporary_meta, meta_path)
            base.hashes = hashes_by_column
    return base
