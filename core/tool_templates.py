import re
from typing import Any

from .models import ProjectApproval, ProjectNotification, ProjectState, ToolExecutionLog


SAFE_TOOL_TEMPLATES = {
    "update_sponsor": {
        "name": "update_sponsor",
        "description": "Update a sponsor commitment value in a controlled record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sponsor_id": {"type": "string"},
                "new_amount": {"type": "number"},
                "sponsor_name": {"type": "string"},
            },
            "required": ["sponsor_id", "new_amount"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "sponsor_id": {"type": "string"}, "new_amount": {"type": "number"}}},
        "risk_level": "high",
        "permissions": ["write"],
        "verification": "Record must be persisted and amount validated against the previous value.",
    },
    "update_budget": {
        "name": "update_budget",
        "description": "Adjust a project budget value by a numeric delta.",
        "input_schema": {
            "type": "object",
            "properties": {"line_id": {"type": "string"}, "delta": {"type": "number"}, "label": {"type": "string"}},
            "required": ["line_id", "delta"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "line_id": {"type": "string"}, "delta": {"type": "number"}}},
        "risk_level": "high",
        "permissions": ["write"],
        "verification": "Budget snapshot must reflect the delta and be consistent with the project totals.",
    },
    "flag_promotion": {
        "name": "flag_promotion",
        "description": "Update the sponsor deliverable tier.",
        "input_schema": {
            "type": "object",
            "properties": {"sponsor_id": {"type": "string"}, "new_tier": {"type": "string"}},
            "required": ["sponsor_id", "new_tier"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "sponsor_id": {"type": "string"}, "new_tier": {"type": "string"}}},
        "risk_level": "medium",
        "permissions": ["write"],
        "verification": "Promotion tier must be persisted and mapped to the sponsor record.",
    },
    "manage_approvals": {
        "name": "manage_approvals",
        "description": "Create a controlled approval record for a project item.",
        "input_schema": {
            "type": "object",
            "properties": {"item": {"type": "string"}, "approver": {"type": "string"}, "notes": {"type": "string"}},
            "required": ["item", "approver"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "item": {"type": "string"}, "approver": {"type": "string"}}},
        "risk_level": "low",
        "permissions": ["write"],
        "verification": "Approval record must be created with item and approver metadata.",
    },
    "draft_email": {
        "name": "draft_email",
        "description": "Persist a draft communication for later review or dispatch.",
        "input_schema": {
            "type": "object",
            "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "subject", "body"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "recipient": {"type": "string"}, "subject": {"type": "string"}}},
        "risk_level": "low",
        "permissions": ["draft"],
        "verification": "Draft email record must be saved with the exact recipient and subject.",
    },
    "create_student": {
        "name": "create_student",
        "description": "Create a student record in the project state store.",
        "input_schema": {
            "type": "object",
            "properties": {"student_id": {"type": "string"}, "name": {"type": "string"}, "program": {"type": "string"}, "year": {"type": "number"}},
            "required": ["student_id", "name", "program", "year"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "student_id": {"type": "string"}}},
        "risk_level": "medium",
        "permissions": ["write"],
        "verification": "Student entity must exist in project state with the expected program and year.",
    },
    "mark_attendance": {
        "name": "mark_attendance",
        "description": "Set attendance state for a student.",
        "input_schema": {
            "type": "object",
            "properties": {"student_id": {"type": "string"}, "status": {"type": "string"}, "course": {"type": "string"}},
            "required": ["student_id", "status"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "student_id": {"type": "string"}, "attendance": {"type": "string"}}},
        "risk_level": "low",
        "permissions": ["write"],
        "verification": "Attendance must be recorded for the targeted student and course context.",
    },
    "calculate_fees": {
        "name": "calculate_fees",
        "description": "Compute student fee due and persist results.",
        "input_schema": {
            "type": "object",
            "properties": {"student_id": {"type": "string"}, "base_amount": {"type": "number"}, "late_fee": {"type": "number"}},
            "required": ["student_id"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "student_id": {"type": "string"}, "total": {"type": "number"}}},
        "risk_level": "low",
        "permissions": ["read", "write"],
        "verification": "Fee total must be computed as base plus late fee and persisted.",
    },
    "generate_timetable": {
        "name": "generate_timetable",
        "description": "Generate a timetable snapshot from a constrained dataset.",
        "input_schema": {
            "type": "object",
            "properties": {"term": {"type": "string"}, "constraints": {"type": "object"}},
            "required": ["term", "constraints"],
        },
        "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "term": {"type": "string"}, "conflicts": {"type": "number"}}},
        "risk_level": "high",
        "permissions": ["write"],
        "verification": "Generated timetable must be persisted and contain zero conflict count.",
    },
}


def _validate_payload(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = SAFE_TOOL_TEMPLATES.get(tool_name)
    if spec is None:
        raise ValueError(f"Unsupported tool template: {tool_name}")
    if not isinstance(payload, dict):
        raise ValueError(f"Tool payload for {tool_name} must be an object")
    for field in spec["input_schema"].get("required", []):
        if field not in payload:
            raise ValueError(f"Missing required field '{field}' for tool '{tool_name}'")
    return payload


def _get_state(project, entity: str, record_key: str) -> ProjectState:
    state, _ = ProjectState.objects.get_or_create(project=project, entity=entity, external_id=record_key)
    return state


def _set_state(project, entity: str, record_key: str, payload: dict[str, Any]) -> ProjectState:
    state = _get_state(project, entity, record_key)
    state.payload = {**state.payload, **payload}
    state.save(update_fields=["payload", "updated_at"])
    return state


def execute_safe_template(project, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    clean = _validate_payload(tool_name, payload or {})

    if tool_name == "update_sponsor":
        sponsor_id = str(clean["sponsor_id"]).strip()
        amount = float(clean["new_amount"])
        state = _set_state(project, "sponsor", sponsor_id, {"name": clean.get("sponsor_name", "Acme Corporation"), "current_amount": amount, "status": "updated"})
        return {"status": "updated", "sponsor_id": sponsor_id, "new_amount": amount, "record_id": str(state.id)}

    if tool_name == "update_budget":
        line_id = str(clean["line_id"]).strip()
        delta = float(clean["delta"])
        state = _set_state(project, "budget", line_id, {"line_id": line_id, "delta": delta, "label": clean.get("label", line_id), "status": "updated"})
        return {"status": "updated", "line_id": line_id, "delta": delta, "record_id": str(state.id)}

    if tool_name == "flag_promotion":
        sponsor_id = str(clean["sponsor_id"]).strip()
        tier = str(clean["new_tier"]).strip()
        state = _set_state(project, "promotion", sponsor_id, {"sponsor_id": sponsor_id, "new_tier": tier, "status": "flagged"})
        return {"status": "flagged", "sponsor_id": sponsor_id, "new_tier": tier, "record_id": str(state.id)}

    if tool_name == "manage_approvals":
        approval = ProjectApproval.objects.create(
            project=project,
            item=str(clean["item"]).strip(),
            approver=str(clean["approver"]).strip(),
            status="pending",
            notes=clean.get("notes", ""),
        )
        return {"status": "pending", "item": approval.item, "approver": approval.approver, "approval_id": str(approval.id)}

    if tool_name == "draft_email":
        email = ProjectNotification.objects.create(
            project=project,
            channel="email",
            recipient=str(clean["to"]).strip(),
            subject=str(clean["subject"]).strip(),
            body=str(clean["body"]).strip(),
            status="draft",
        )
        return {"status": "draft", "recipient": email.recipient, "subject": email.subject, "notification_id": str(email.id)}

    if tool_name == "create_student":
        student_id = str(clean["student_id"]).strip()
        state = _set_state(project, "student", student_id, {
            "student_id": student_id,
            "name": clean["name"],
            "program": clean["program"],
            "year": int(clean["year"]),
            "status": "created",
        })
        return {"status": "created", "student_id": student_id, "record_id": str(state.id)}

    if tool_name == "mark_attendance":
        student_id = str(clean["student_id"]).strip()
        state = _get_state(project, "student", student_id)
        attendance = {"status": str(clean["status"]).strip(), "course": clean.get("course", "general"), "updated": True}
        state.payload = {**state.payload, "attendance": attendance}
        state.save(update_fields=["payload", "updated_at"])
        return {"status": "updated", "student_id": student_id, "attendance": attendance["status"], "record_id": str(state.id)}

    if tool_name == "calculate_fees":
        student_id = str(clean["student_id"]).strip()
        state = _get_state(project, "student", student_id)
        base_amount = float(clean.get("base_amount", 50000))
        late_fee = float(clean.get("late_fee", 0))
        total = base_amount + late_fee
        state.payload = {**state.payload, "fees": {"base_amount": base_amount, "late_fee": late_fee, "total": total}}
        state.save(update_fields=["payload", "updated_at"])
        return {"status": "calculated", "student_id": student_id, "total": total, "record_id": str(state.id)}

    if tool_name == "generate_timetable":
        term = str(clean["term"]).strip()
        constraints = clean.get("constraints", {}) or {}
        conflict_count = 0
        if isinstance(constraints, dict):
            conflict_count = int(constraints.get("conflict_count", 0))
        state = _set_state(project, "timetable", term, {"term": term, "constraints": constraints, "conflicts": conflict_count, "status": "generated"})
        return {"status": "generated", "term": term, "conflicts": conflict_count, "record_id": str(state.id)}

    raise ValueError(f"Unsupported tool template: {tool_name}")


def get_registered_templates() -> dict[str, dict[str, Any]]:
    return SAFE_TOOL_TEMPLATES.copy()


def create_tool_execution_log(project, tool_name: str, request_payload: dict[str, Any], result: dict[str, Any], status: str = "success") -> ToolExecutionLog:
    log = ToolExecutionLog.objects.create(
        project=project,
        tool_name=tool_name,
        request_payload=request_payload,
        result_payload=result,
        status=status,
    )
    return log
