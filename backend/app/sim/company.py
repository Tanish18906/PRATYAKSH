"""Fixed fictional company entities and access matrix."""

from .names import FIRST_NAMES, LAST_NAMES


SYSTEMS = (
    ("customer-db", False), ("claims-api", False), ("crm", False),
    ("bi-warehouse", False), ("notebook-server", False), ("partner-sftp", True),
    ("object-store", True), ("ticketing", False), ("email-gateway", True),
)
EXTERNALS = ("telegram-leak-channel", "file-share-site", "personal-cloud-drive",
             "unknown-host", "vendor-nimbus")
ACCESS = {
    "analyst": ("bi-warehouse", "notebook-server"),
    "bi-admin": ("bi-warehouse", "notebook-server", "object-store"),
    "engineer": ("customer-db", "claims-api", "bi-warehouse", "object-store", "ticketing"),
    "marketing": ("crm", "email-gateway", "partner-sftp"),
    "support": ("ticketing", "crm", "claims-api"),
    "contractor": ("customer-db", "notebook-server"),
}
FIXED_USERS = (
    ("ravi-menon", "Ravi Menon", "analyst", "Data & BI"),
    ("meena-iyer", "Meena Iyer", "bi-admin", "Data & BI"),
    ("arjun-das", "Arjun Das", "contractor", "External"),
    ("kavya-rao", "Kavya Rao", "marketing", "Growth"),
)
GENERATED_ROLES = ("analyst",) * 4 + ("engineer",) * 4 + ("marketing",) * 2 + (
    "support",) * 4 + ("contractor", "bi-admin")
SERVICES = (
    ("etl-nightly", ("customer-db", "bi-warehouse"), "Platform"),
    ("partner-api-key-7", ("bi-warehouse", "partner-sftp", "crm"), "Partners"),
    ("backup-svc", ("customer-db", "object-store"), "Platform"),
)
CUSTOMER_COLUMNS = ("customer_id", "full_name", "email", "phone", "dob", "city", "state",
                    "signup_date", "created_at", "policy_no", "premium_tier")


def make_company(scale: str, arrivals_per_hour: float) -> dict:
    locations = []
    sources = []
    for slug, egress in SYSTEMS:
        location_id = f"sys:{slug}"
        source_id = f"src:{slug}"
        locations.append({"id": location_id, "kind": "system", "name": slug.replace("-", " ").title(),
                          "owner_actor": None, "monitored": True, "log_source": source_id,
                          "egress_capable": egress})
        sources.append({"id": source_id, "name": f"{slug} audit", "location": location_id})

    actors = []
    users = FIXED_USERS + tuple(
        (f"{first.lower()}-{last.lower()}", f"{first} {last}", role,
         {"analyst": "Data & BI", "bi-admin": "Data & BI", "engineer": "Platform",
          "marketing": "Growth", "support": "Operations", "contractor": "External"}[role])
        for first, last, role in zip(FIRST_NAMES, LAST_NAMES, GENERATED_ROLES)
    )
    for slug, name, role, team in users:
        actor_id = f"act:{slug}"
        endpoint_id = f"ep:{slug}"
        actors.append({"id": actor_id, "kind": "user", "name": name, "role": role,
                       "team": team, "access": [f"sys:{s}" for s in ACCESS[role]] + [endpoint_id]})
        locations.append({"id": endpoint_id, "kind": "endpoint", "name": f"{name} laptop",
                          "owner_actor": actor_id, "monitored": False, "log_source": None,
                          "egress_capable": True})
    for slug, access, team in SERVICES:
        actors.append({"id": f"act:{slug}", "kind": "service", "name": slug,
                       "role": "service", "team": team,
                       "access": [f"sys:{s}" for s in access]})
    for slug in EXTERNALS:
        locations.append({"id": f"ext:{slug}", "kind": "external", "name": slug.replace("-", " ").title(),
                          "owner_actor": None, "monitored": False, "log_source": None,
                          "egress_capable": False})
    datasets = [
        {"id": "ds:customers", "name": "Customers", "system": "sys:customer-db",
         "columns": list(CUSTOMER_COLUMNS),
         "identifier_columns": ["customer_id", "email", "phone", "policy_no"],
         "row_count": 310_000 if scale == "demo" else 31_000,
         "sensitivity": "high", "arrivals_per_hour": arrivals_per_hour},
        {"id": "ds:claims", "name": "Claims", "system": "sys:claims-api",
         "columns": ["claim_id", "customer_id", "amount", "diagnosis_code", "claim_date"],
         "identifier_columns": ["customer_id"], "row_count": 90_000 if scale == "demo" else 9_000,
         "sensitivity": "high", "arrivals_per_hour": 2.0},
        {"id": "ds:marketing-leads", "name": "Marketing Leads", "system": "sys:crm",
         "columns": ["lead_id", "full_name", "email", "city"],
         "identifier_columns": ["email"], "row_count": 62_000 if scale == "demo" else 6_200,
         "sensitivity": "medium", "arrivals_per_hour": 1.0},
    ]
    return {"locations": locations, "log_sources": sources, "actors": actors, "datasets": datasets}
