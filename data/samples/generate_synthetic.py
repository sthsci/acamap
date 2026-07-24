"""Generate synthetic demonstration data for Lab Vibes London.

Deterministic, bilingual (English + Chinese), and entirely fictional: it
contains NO real RedNote/Xiaohongshu posts and no real people. It exists so the
pipeline and website work immediately without any real dataset.

The generator emits rows for the raw-input schema, including:
  * labs above the publication threshold and labs deliberately below it,
  * a few items that should be caught by the moderation pass,
  * repeated engagement snapshots for some posts (longitudinal-ready).
  * provided, catalogue-matched, safely inferred and ambiguous campus data.

Run:  python data/samples/generate_synthetic.py
Writes synthetic_posts.csv and synthetic_posts.json next to this file.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent

FIELDS = [
    "source", "post_id", "comment_id", "author_id", "text",
    "posted_at", "collected_at", "institution_id", "department", "lab_name",
    "campus_id", "campus_name_raw", "campus_assignment_method",
    "campus_assignment_confidence",
    "researcher_name", "source_url", "likes_at_collection", "comments_at_collection",
]

POSITIVE = [
    "The supervisor is supportive and gives helpful, constructive feedback.",
    "Great mentorship here — my mentor is approachable and encouraging.",
    "Very collaborative and friendly group culture overall.",
    "Well-funded lab with good equipment and plenty of resources.",
    "There is real research freedom and flexible working arrangements.",
    "导师很支持，实验室氛围友好。",
    "组里资源充足，设备很好，导师也很有帮助。",
]
CHALLENGE = [
    "The hours can be long and the workload is heavy at times.",
    "There is noticeable pressure around deadlines and high expectations.",
    "Communication about expectations is sometimes unclear.",
    "A fair amount of administrative overhead slows things down.",
    "It can feel competitive in the run-up to paper deadlines.",
    "压力有点大，工作量比较多。",
    "有时候沟通不太清楚，期望也不明确。",
]
NEUTRAL = [
    "The group is quite international, with members from many countries.",
    "The work is interdisciplinary, spanning several departments.",
    "It is a fairly large group with many PhD students and postdocs.",
    "组里很国际化，成员来自不同国家。",
    "研究偏跨学科合作。",
]

# reason-triggering (fictional) items to exercise the moderation queue
WITHHELD = [
    "There were rumours of harassment involving a senior member of the group.",
    "某老师涉嫌学术造假，数据被质疑。",
    "Honestly the PI is an idiot and completely incompetent.",
    "I was diagnosed with depression during my time in this lab.",
]

_EECS = "Electronic Engineering and Computer Science"

# lab -> (clean_items, distinct_authors, withheld_items, longitudinal_posts)
LAB_SPECS: dict[tuple[str, str, str], tuple[int, int, int, int]] = {
    ("imperial", "Computing", "Adaptive Systems Lab"): (9, 5, 2, 3),
    ("imperial", "Computing", "Visual Computing Group"): (6, 4, 0, 1),
    ("imperial", "Bioengineering", "Neurotechnology Lab"): (3, 2, 0, 0),
    ("ucl", "Computer Science", "Machine Reasoning Group"): (8, 4, 1, 2),
    ("ucl", "Neuroscience", "Cognitive Circuits Lab"): (7, 3, 0, 1),
    ("ucl", "Neuroscience", "Imaging Analytics Lab"): (0, 0, 0, 0),
    ("kcl", "Informatics", "Distributed Systems Group"): (4, 3, 0, 0),
    ("kcl", "Psychology", "Affective Science Lab"): (2, 2, 0, 0),
    ("qmul", _EECS, "Networks Research Lab"): (5, 3, 0, 1),
    ("qmul", _EECS, "Cognitive Science Group"): (4, 2, 0, 0),
    ("lshtm", "Infectious Disease Epidemiology", "Epidemic Modelling Group"): (6, 3, 1, 1),
    ("lshtm", "Global Health", "Health Systems Lab"): (5, 2, 0, 0),
    ("crick", "Structural Biology", "Molecular Machines Lab"): (1, 1, 0, 0),
    ("crick", "Computational Biology", "Genome Analytics Lab"): (7, 4, 0, 2),
}

LAB_CAMPUSES: dict[tuple[str, str, str], list[tuple[str, str]]] = {
    ("imperial", "Computing", "Adaptive Systems Lab"): [
        ("imperial-south-kensington", "South Kensington"),
        ("imperial-white-city", "White City"),
    ],
    ("imperial", "Computing", "Visual Computing Group"): [
        ("imperial-white-city", "White City")
    ],
    ("imperial", "Bioengineering", "Neurotechnology Lab"): [
        ("imperial-south-kensington", "South Kensington")
    ],
    ("ucl", "Computer Science", "Machine Reasoning Group"): [
        ("ucl-bloomsbury", "Bloomsbury"),
        ("ucl-east", "UCL East"),
    ],
    ("ucl", "Neuroscience", "Cognitive Circuits Lab"): [
        ("ucl-queen-square", "Queen Square")
    ],
    ("ucl", "Neuroscience", "Imaging Analytics Lab"): [
        ("ucl-queen-square", "Queen Square"),
        ("ucl-royal-free", "Royal Free"),
    ],
    ("kcl", "Informatics", "Distributed Systems Group"): [
        ("kcl-strand", "Strand"),
        ("kcl-waterloo", "Waterloo"),
    ],
    ("kcl", "Psychology", "Affective Science Lab"): [
        ("kcl-denmark-hill", "Denmark Hill")
    ],
    ("qmul", _EECS, "Networks Research Lab"): [("qmul-mile-end", "Mile End")],
    ("qmul", _EECS, "Cognitive Science Group"): [
        ("qmul-mile-end", "Mile End"),
        ("qmul-whitechapel", "Whitechapel"),
    ],
    ("lshtm", "Infectious Disease Epidemiology", "Epidemic Modelling Group"): [
        ("lshtm-keppel-street", "Keppel Street"),
        ("lshtm-tavistock-place", "Tavistock Place"),
    ],
    ("lshtm", "Global Health", "Health Systems Lab"): [
        ("lshtm-tavistock-place", "Tavistock Place")
    ],
    ("crick", "Structural Biology", "Molecular Machines Lab"): [
        ("crick-st-pancras", "St Pancras")
    ],
    ("crick", "Computational Biology", "Genome Analytics Lab"): [
        ("crick-st-pancras", "St Pancras")
    ],
}

BASE_POSTED = datetime(2025, 9, 1, 9, 0, 0)
COLLECTED_1 = datetime(2026, 2, 1, 12, 0, 0)
COLLECTED_2 = datetime(2026, 3, 1, 12, 0, 0)


def _text_for(index: int) -> str:
    positive = POSITIVE[index % len(POSITIVE)]
    other = (
        CHALLENGE[index % len(CHALLENGE)]
        if index % 2 == 0
        else NEUTRAL[index % len(NEUTRAL)]
    )
    return f"{positive} {other}"


def generate() -> list[dict]:
    rows: list[dict] = []
    counter = 0

    def add_row(**kwargs) -> None:
        row = {field: "" for field in FIELDS}
        row.update(kwargs)
        rows.append(row)

    for (institution_id, department, lab), spec in LAB_SPECS.items():
        clean, authors, withheld, longitudinal = spec
        campuses = LAB_CAMPUSES[(institution_id, department, lab)]
        for i in range(clean):
            counter += 1
            pid = f"syn-{counter:04d}"
            comment_id = f"c-{counter:04d}" if i < 3 else ""
            author = f"auth-{institution_id[:3]}-{i % max(authors, 1):02d}"
            posted = BASE_POSTED + timedelta(days=counter * 2, hours=i)
            campus_id = ""
            campus_name_raw = ""
            if i == 0:
                campus_id = campuses[0][0]  # explicitly provided
            elif i == 1:
                campus_name_raw = campuses[-1][1]  # canonical catalogue match
            elif len(campuses) == 1:
                # Safely inferred from the single-campus lab.
                pass
            elif i == 2:
                # Ambiguous multi-campus lab: must remain unspecified.
                pass
            else:
                campus_id = campuses[i % len(campuses)][0]
            add_row(
                source="rednote-synthetic",
                post_id=pid,
                comment_id=comment_id,
                author_id=author,
                text=_text_for(counter),
                posted_at=posted.isoformat(),
                collected_at=COLLECTED_1.isoformat(),
                institution_id=institution_id,
                department=department,
                lab_name=lab,
                campus_id=campus_id,
                campus_name_raw=campus_name_raw,
                campus_assignment_method="unspecified",
                campus_assignment_confidence="",
                researcher_name="Group Lead" if i == 0 else "",
                source_url=f"https://example.invalid/synthetic/post/{pid}",
                likes_at_collection=10 + (counter % 40),
                comments_at_collection=counter % 6,
            )
            # longitudinal: a later engagement snapshot for the first few posts
            if i < longitudinal:
                add_row(
                    source="rednote-synthetic",
                    post_id=pid,
                    comment_id=comment_id,
                    author_id=author,
                    text=_text_for(counter),
                    posted_at=posted.isoformat(),
                    collected_at=COLLECTED_2.isoformat(),
                    institution_id=institution_id,
                    department=department,
                    lab_name=lab,
                    campus_id=campus_id,
                    campus_name_raw=campus_name_raw,
                    campus_assignment_method="unspecified",
                    campus_assignment_confidence="",
                    researcher_name="",
                    source_url=f"https://example.invalid/synthetic/post/{pid}",
                    likes_at_collection=25 + (counter % 40),
                    comments_at_collection=2 + counter % 6,
                )
        for j in range(withheld):
            counter += 1
            pid = f"syn-{counter:04d}"
            add_row(
                source="rednote-synthetic",
                post_id=pid,
                comment_id=f"c-{counter:04d}",
                author_id=f"auth-{institution_id[:3]}-w{j:02d}",
                text=WITHHELD[(counter) % len(WITHHELD)],
                posted_at=(BASE_POSTED + timedelta(days=counter * 2)).isoformat(),
                collected_at=COLLECTED_1.isoformat(),
                institution_id=institution_id,
                department=department,
                lab_name=lab,
                campus_id=campuses[0][0] if len(campuses) == 1 else "",
                campus_name_raw="",
                campus_assignment_method="unspecified",
                campus_assignment_confidence="",
                researcher_name="",
                source_url=f"https://example.invalid/synthetic/comment/{pid}",
                likes_at_collection=3 + counter % 10,
                comments_at_collection=counter % 3,
            )
    return rows


def main() -> None:
    rows = generate()
    csv_path = HERE / "synthetic_posts.csv"
    json_path = HERE / "synthetic_posts.json"

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    typed = []
    for row in rows:
        record = dict(row)
        for key in (
            "comment_id",
            "campus_id",
            "campus_name_raw",
            "campus_assignment_confidence",
            "researcher_name",
        ):
            if record[key] == "":
                record[key] = None
        record["likes_at_collection"] = int(record["likes_at_collection"])
        record["comments_at_collection"] = int(record["comments_at_collection"])
        typed.append(record)
    json_path.write_text(
        json.dumps(typed, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"wrote {len(rows)} rows -> {csv_path.name}, {json_path.name}")


if __name__ == "__main__":
    main()
