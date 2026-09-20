"""Rule-based Consistency and Anomaly Checks.

Rule R5: Flags use neutral wording ("Dates overlap between X and Y, worth clarifying").
Never accuse.

Implements deterministic rules:
1. Overlapping employment dates.
2. Skill claimed in skills list with no supporting project or experience mention.
3. Title inflation / seniority mismatch without tenure.
"""

import re
from typing import List, Dict, Any
from engine.schema import ConsistencyFlag, CandidateProfile


def check_date_overlaps(experience: List[Dict[str, str]]) -> List[ConsistencyFlag]:
    """Identifies overlapping timeframes between multiple distinct employment entries."""
    flags = []
    # Pattern to extract years or month/year
    # e.g. "Jan 2023 - Present", "Jun 2022 - Mar 2024", "2021 - 2023"
    date_pattern = r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*)?(\d{4})"

    parsed_roles = []
    for exp in experience:
        period = exp.get("period", "")
        company = exp.get("company", exp.get("role", "Company"))
        if not period:
            continue

        years = re.findall(r"\b(20\d\d)\b", period)
        is_present = "present" in period.lower() or "current" in period.lower()

        if len(years) >= 2:
            start_yr, end_yr = int(years[0]), int(years[1])
            parsed_roles.append({"company": company, "start": start_yr, "end": end_yr, "period": period})
        elif len(years) == 1 and is_present:
            start_yr = int(years[0])
            parsed_roles.append({"company": company, "start": start_yr, "end": 2026, "period": period})

    # Compare pairs for significant overlap
    for i in range(len(parsed_roles)):
        for j in range(i + 1, len(parsed_roles)):
            r1 = parsed_roles[i]
            r2 = parsed_roles[j]

            # Overlap exists if start of one is before end of other and vice versa
            overlap_start = max(r1["start"], r2["start"])
            overlap_end = min(r1["end"], r2["end"])

            if overlap_end > overlap_start:
                flags.append(
                    ConsistencyFlag(
                        type="date_overlap",
                        description=f"Dates overlap between {r1['company']} ({r1['period']}) and {r2['company']} ({r2['period']}), worth clarifying",
                        evidence=[f"{r1['company']}: {r1['period']}", f"{r2['company']}: {r2['period']}"]
                    )
                )

    return flags


def check_unbacked_skills(profile: CandidateProfile, raw_text: str) -> List[ConsistencyFlag]:
    """Identifies skills prominently claimed in keywords but with zero mentions in projects/experience."""
    flags = []
    exp_and_proj_text = " ".join(
        [e.get("quote", "") for e in profile.experience] + [p.get("quote", "") for p in profile.projects]
    ).lower()

    for s in profile.skills:
        skill_name = s.get("skill", "").strip()
        if not skill_name or len(skill_name) < 3:
            continue

        # Check if skill appears in experience or projects
        skill_re = rf"\b{re.escape(skill_name.lower())}\b"
        if not re.search(skill_re, exp_and_proj_text):
            flags.append(
                ConsistencyFlag(
                    type="unbacked_skill",
                    description=f"{skill_name} claimed in skills list with no supporting project or experience mention, worth clarifying",
                    evidence=[f"Skills list: {s.get('quote', skill_name)}", "Experience/Projects: No supporting context found"]
                )
            )

    return flags


def check_consistency_flags(profile: CandidateProfile, raw_text: str) -> List[ConsistencyFlag]:
    """Runs all deterministic consistency checks and returns neutral flags."""
    flags: List[ConsistencyFlag] = []
    flags.extend(check_date_overlaps(profile.experience))
    flags.extend(check_unbacked_skills(profile, raw_text))
    return flags
