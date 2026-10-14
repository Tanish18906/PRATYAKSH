"""Format profiles and deterministic rendering for synthetic export rows."""

import csv
import hashlib
import io
import re
from datetime import date


STYLES = {
    "ETL": (",", "minimal", "snake", "LF", "utf-8", "", "e164_dash", "lower", "title", "iso"),
    "CONTRACTOR": (",", "all", "title", "CRLF", "utf-8-bom", "NULL", "digits10", "mixed", "upper", "dmy_slash"),
    "MARKETING": (";", "minimal", "title", "LF", "utf-8", "N/A", "intl_spaced", "lower", "title", "mdy_dash_yy"),
    "NOTEBOOK": (",", "minimal", "camel", "LF", "utf-8", "", "digits10", "lower", "lower", "iso"),
}


def format_profile(style: str, columns: list[str]) -> dict:
    delimiter, quoting, header_case, line_ending, encoding, null_token, phone, email, name, dates = STYLES[style]
    column_styles = {}
    for column in columns:
        if column == "phone":
            column_styles[column] = {"style": phone}
        elif column == "email":
            column_styles[column] = {"case": email}
        elif column == "full_name":
            column_styles[column] = {"case": name}
        elif column in ("signup_date", "dob"):
            column_styles[column] = {"style": dates}
        elif column == "created_at":
            column_styles[column] = {"style": "iso"}
    return {
        "delimiter": delimiter,
        "quoting": quoting,
        "header_case": header_case,
        "line_ending": line_ending,
        "encoding": encoding,
        "null_token": null_token,
        "columns": column_styles,
    }


def render_value(column: str, value, style: str, row_index: int = 0) -> str:
    profile = format_profile(style, [column])
    if value is None or value == "":
        return profile["null_token"]
    value = str(value)
    if column == "phone":
        digits = re.sub(r"\D", "", value)[-10:]
        phone_style = profile["columns"][column]["style"]
        if phone_style == "e164_dash":
            return f"+91-{digits}"
        if phone_style == "intl_spaced":
            return f"+91 {digits[:5]} {digits[5:]}"
        return digits
    if column == "email":
        value = value.lower()
        if profile["columns"][column]["case"] == "mixed":
            # Row index gives a stable, roughly even choice without shared RNG state.
            if hashlib.sha256(str(row_index).encode()).digest()[0] & 1:
                value = value[:1].upper() + value[1:]
        return value
    if column == "full_name":
        case = profile["columns"][column]["case"]
        return {"title": str.title, "upper": str.upper, "lower": str.lower}[case](value)
    if column in ("signup_date", "dob"):
        day = date.fromisoformat(value[:10])
        date_style = profile["columns"][column]["style"]
        if date_style == "dmy_slash":
            return day.strftime("%d/%m/%Y")
        if date_style == "mdy_dash_yy":
            return day.strftime("%m-%d-%y")
        return day.isoformat()
    return value


def render_csv(rows, columns: list[str], style: str) -> bytes:
    """Render an export using its profile; rows may be any iterable of mappings."""
    profile = format_profile(style, columns)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=profile["delimiter"],
                        quoting=csv.QUOTE_ALL if profile["quoting"] == "all" else csv.QUOTE_MINIMAL,
                        lineterminator="\r\n" if profile["line_ending"] == "CRLF" else "\n")
    header_case = profile["header_case"]
    if header_case == "title":
        headers = [column.replace("_", " ").title() for column in columns]
    elif header_case == "upper":
        headers = [column.upper() for column in columns]
    elif header_case == "camel":
        headers = [column.split("_")[0] + "".join(part.title() for part in column.split("_")[1:])
                   for column in columns]
    else:
        headers = columns
    writer.writerow(headers)
    for index, row in enumerate(rows):
        writer.writerow([render_value(column, row.get(column), style, index) for column in columns])
    encoding = "utf-8-sig" if profile["encoding"] == "utf-8-bom" else profile["encoding"]
    return buffer.getvalue().encode(encoding)
