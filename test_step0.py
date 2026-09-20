from models import Requirement, Evidence, RequirementRecord, Question, AuditEntry, HistoryItem
from audit import log_entry, get_audit_trail

def test_models_and_audit():
    # 1. Test Requirement
    req = Requirement(
        id="REQ-1",
        text="4+ years backend development with Python",
        type="must",
        weight=1.0
    )
    assert req.id == "REQ-1"
    assert req.type == "must"

    # 2. Test Evidence
    ev = Evidence(
        source="resume",
        quote="Led a team of engineers to deliver high-impact core initiatives on schedule."
    )
    assert ev.source == "resume"

    # 3. Test RequirementRecord
    rec = RequirementRecord(
        requirement_id="REQ-1",
        status="partial",
        confidence="medium",
        evidence=[ev],
        history=[
            HistoryItem(
                old_status="missing",
                new_status="partial",
                reason="Found initial resume quote"
            )
        ]
    )
    assert rec.status == "partial"
    assert len(rec.evidence) == 1
    assert len(rec.history) == 1

    # 4. Test Question
    q = Question(id="Q-1", requirement_id="REQ-1", text="Can you elaborate on your Python experience?")
    assert q.requirement_id == "REQ-1"

    # 5. Test Audit log
    entry = log_entry(
        insight_id="INSIGHT-001",
        step="test_step",
        inputs_used=["test_input"],
        prompt_version="v1",
        output={"status": "met"}
    )
    assert entry.insight_id == "INSIGHT-001"

    trail = get_audit_trail()
    assert any(e["insight_id"] == "INSIGHT-001" for e in trail)

    print("ALL STEP 0 MODEL & AUDIT TESTS PASSED!")

if __name__ == "__main__":
    test_models_and_audit()
