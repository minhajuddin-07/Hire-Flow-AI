import pandas as pd
from models import Requirement, ExtractedRequirements
from audit import log_entry, get_audit_trail

def test_persistence_and_edits():
    initial_reqs = [
        {"id": "REQ-1", "text": "4+ years Python experience", "type": "must", "weight": 2.0},
        {"id": "REQ-2", "text": "Experience with Docker and Kubernetes", "type": "nice", "weight": 1.0},
        {"id": "REQ-3", "text": "Distributed REST APIs with FastAPI", "type": "must", "weight": 1.8},
    ]

    # Convert to DataFrame (Streamlit data_editor format)
    df = pd.DataFrame(initial_reqs)
    assert len(df) == 3

    # Simulate recruiter edits:
    # 1. Edit text of REQ-1
    df.loc[df["id"] == "REQ-1", "text"] = "5+ years backend Python development"
    # 2. Change REQ-2 from 'nice' to 'must'
    df.loc[df["id"] == "REQ-2", "type"] = "must"
    # 3. Add new requirement REQ-4
    new_row = pd.DataFrame([{"id": "REQ-4", "text": "AWS Cloud experience", "type": "nice", "weight": 1.2}])
    df = pd.concat([df, new_row], ignore_index=True)
    # 4. Delete REQ-3
    df = df[df["id"] != "REQ-3"].reset_index(drop=True)

    edited_records = df.to_dict(orient="records")
    assert len(edited_records) == 3
    assert edited_records[0]["text"] == "5+ years backend Python development"
    assert edited_records[1]["type"] == "must"
    assert edited_records[2]["id"] == "REQ-4"

    # Validate against Pydantic Requirement model
    pydantic_reqs = [Requirement(**r) for r in edited_records]
    assert len(pydantic_reqs) == 3

    # Log to audit trail
    log_entry(
        insight_id="TEST-MANUAL-EDIT",
        step="manual_edit_requirements",
        inputs_used=[{"count": len(edited_records)}],
        prompt_version="manual",
        output=edited_records,
    )

    trail = get_audit_trail()
    assert any(e["insight_id"] == "TEST-MANUAL-EDIT" for e in trail)

    print("ALL PERSISTENCE AND EDITING TESTS PASSED!")

if __name__ == "__main__":
    test_persistence_and_edits()
