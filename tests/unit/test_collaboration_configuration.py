"""Check machine-readable labels and their consumers without contacting GitHub."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_label_catalog_has_valid_unique_payloads() -> None:
    labels = json.loads((ROOT / ".github/labels.json").read_text(encoding="utf-8"))
    assert isinstance(labels, list) and labels
    names = []
    for label in labels:
        assert set(label) == {"name", "color", "description"}
        assert isinstance(label["name"], str) and label["name"] == label["name"].strip()
        assert 0 < len(label["name"]) <= 50
        assert re.fullmatch(r"[0-9a-fA-F]{6}", label["color"])
        assert isinstance(label["description"], str) and label["description"].strip()
        assert len(label["description"]) <= 100
        names.append(label["name"].casefold())
    assert len(names) == len(set(names)), "Label names must be unique ignoring case"


def test_issue_templates_reference_defined_labels() -> None:
    catalog = json.loads((ROOT / ".github/labels.json").read_text(encoding="utf-8"))
    names = {label["name"] for label in catalog}
    templates = list((ROOT / ".github/ISSUE_TEMPLATE").glob("*.md"))
    assert templates
    for template in templates:
        frontmatter = template.read_text(encoding="utf-8").split("---", 2)[1]
        line = re.search(r"^labels:\s*(.+)$", frontmatter, re.MULTILINE)
        assert line, f"Missing label declaration in {template.name}"
        referenced = {label.strip() for label in line.group(1).split(",")}
        assert referenced <= names, f"Undefined labels in {template.name}: {referenced - names}"
