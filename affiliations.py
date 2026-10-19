"""Read the affiliation directory without assigning uncertain identities."""

from collections import defaultdict
from dataclasses import dataclass
from html import escape
import re
import unicodedata


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


def name_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize_text(value))


def practitioner_key(first_name: str, last_name: str) -> str:
    return f"{name_key(first_name)}:{name_key(last_name)}"


# Short family names used in the source, checked against the full roster.
# Do not add fuzzy matches here; the Viaux/Viaud variants were confirmed by the owner.
SURNAME_ALIASES = {
    "lauriane:vulliezcoady": ("Vulliez",),
    "angele:manesseconsoli": ("Consoli",),
    "sylvie:viauxsavelon": ("Viaux", "Viaud"),
}

CATEGORY_ORDER = {
    "Instance nationale": 0,
    "Instance internationale": 1,
    "Société savante nationale": 2,
    "Société savante internationale": 3,
    "Réseau": 4,
    "Revue": 5,
    "Organisation": 6,
    "Responsabilité pour l’Université": 7,
    "Filière de soins": 8,
    "Centre d’excellence TND": 9,
}


@dataclass(frozen=True)
class Affiliation:
    label: str
    name: str
    detail: str = ""
    dates: str = ""


@dataclass(frozen=True)
class UnmatchedName:
    name: str
    affiliation: str
    row: int


def category_label(category: str, scope: str) -> str:
    original_category = category
    category = name_key(category)
    international = "international" in normalize_text(scope)
    if category == "instances":
        return "Instance internationale" if international else "Instance nationale"
    if category == "societessavantes":
        return "Société savante internationale" if international else "Société savante nationale"
    if category.startswith("associations"):
        return "Réseau"
    if category.startswith("responsabilites"):
        return "Responsabilité pour l’Université"
    if category.startswith("revues"):
        return "Revue"
    if category.startswith("organisation"):
        return "Organisation"
    if category == "filieresdesoins":
        return "Filière de soins"
    if category.startswith("centresdexcellence"):
        return "Centre d’excellence TND"
    return original_category


def split_people(value: str) -> list[str]:
    """Keep commas inside role descriptions; tolerate a trailing comma."""
    parts, start, depth = [], 0, 0
    for index, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char in ",;\n" and depth == 0:
            if value[start:index].strip():
                parts.append(value[start:index].strip())
            start = index + 1
    if value[start:].strip():
        parts.append(value[start:].strip())
    return parts


def name_index(roster: list[dict]) -> dict[str, set[str]]:
    aliases = defaultdict(set)
    for person in roster:
        first, last = person["Prénom"], person["Nom"]
        key = practitioner_key(first, last)
        first_parts = re.findall(r"[a-z]+", normalize_text(first))
        if not first_parts:
            continue
        initials = "".join(part[0] for part in first_parts)
        for surname in (last, *SURNAME_ALIASES.get(key, ())):
            for given in (first, initials, initials[0]):
                aliases[name_key(given + surname)].add(key)
    return dict(aliases)


def match_person(text: str, aliases: dict[str, set[str]]) -> tuple[str | None, str]:
    # Remember original character positions so roles retain their accents and punctuation.
    normalized, positions = [], []
    for index, char in enumerate(text):
        for letter in name_key(char):
            normalized.append(letter)
            positions.append(index)
    compact = "".join(normalized)
    for alias in sorted(aliases, key=len, reverse=True):
        if not compact.startswith(alias):
            continue
        end = positions[len(alias) - 1] + 1
        # A longer surname must not be silently matched to its prefix.
        if end < len(text) and (text[end].isalpha() or text[end] in "-’'"):
            continue
        matches = aliases[alias]
        if len(matches) != 1:
            return None, text
        detail = text[end:].strip(" ,;\n")
        if detail.startswith("("):
            balanced = detail.count("(") == detail.count(")")
            detail = detail[1:]
            if balanced and detail.endswith(")"):
                detail = detail[:-1]
        return next(iter(matches)), detail.strip()
    return None, text


def build_affiliations(rows: list[list[str]], roster: list[dict]):
    aliases = name_index(roster)
    entries = defaultdict(list)
    unmatched = []
    category = scope = ""
    for row_number, raw_row in enumerate(rows, start=1):
        row = [str(value or "").strip() for value in raw_row]
        row += [""] * max(0, 5 - len(row))
        if row[0]:
            category, scope = row[0], ""
        if row[1]:
            scope = row[1]
        organization, people, dates = row[2:5]
        if not category or not organization or not people or organization == "NOMS":
            continue
        label = category_label(category, scope)
        previous_key = None
        for person_text in split_people(people):
            key, detail = match_person(person_text, aliases)
            if key is None:
                # These comma-separated fragments are roles, not additional people.
                is_role = person_text[:1].islower() or person_text.startswith("International Distinguished Fellow")
                if previous_key and is_role:
                    previous = entries[previous_key][-1]
                    entries[previous_key][-1] = Affiliation(
                        previous.label, previous.name,
                        ", ".join(filter(None, (previous.detail, person_text))), previous.dates,
                    )
                else:
                    unmatched.append(UnmatchedName(person_text, organization, row_number))
                    previous_key = None
                continue
            entries[key].append(Affiliation(label, organization, detail, dates))
            previous_key = key
    # Preserve source order within categories and suppress exact duplicate entries.
    return {
        key: sorted(dict.fromkeys(values), key=lambda entry: CATEGORY_ORDER.get(entry.label, 99))
        for key, values in entries.items()
    }, unmatched


def search_text(person: dict, affiliations: list[Affiliation]) -> str:
    values = [str(person.get(field, "")) for field in ("Prénom", "Nom", "Université", "Corps", "Nomination")]
    values.extend(" ".join((entry.label, entry.name, entry.detail, entry.dates)) for entry in affiliations)
    return normalize_text(" ".join(values))


def matches_search(text: str, query: str) -> bool:
    return all(term in text for term in normalize_text(query).split())


def affiliations_html(entries: list[Affiliation]) -> str:
    if not entries:
        return ""

    def display_text(value: str) -> str:
        return escape("\n".join(line.rstrip(" .…\t") for line in value.strip().splitlines()))

    groups = defaultdict(list)
    for entry in entries:
        detail = f'<span class="affiliation-detail">{display_text(entry.detail)}</span>' if entry.detail else ""
        dates = f'<span class="affiliation-detail">Dates : {display_text(entry.dates)}</span>' if entry.dates else ""
        groups[entry.label].append(f"<li>{display_text(entry.name)}{detail}{dates}</li>")
    content = "".join(
        f'<div class="affiliation-group"><dt>{display_text(label)}</dt><dd><ul>{"".join(items)}</ul></dd></div>'
        for label, items in groups.items()
    )
    body = f"<dl>{content}</dl>"
    return f'<aside class="affiliation-card" aria-label="Affiliations et responsabilités"><h4>Affiliations et responsabilités</h4>{body}</aside>'
