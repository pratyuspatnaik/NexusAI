import json
import os
from datetime import datetime
from typing import Any

from django.db import connection

from .tool_templates import SAFE_TOOL_TEMPLATES, create_tool_execution_log, execute_safe_template, get_registered_templates

try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency
    genai = None


DEFAULT_PROJECTS = {
    "event": {
        "name": "College Event Management",
        "short": "Tech Fest 2026",
        "domain": "Event & sponsorship operations",
        "modules": [
            "Sponsor tracking",
            "Budget management",
            "Promotional deliverables",
            "Approval workflows",
        ],
        "entities": ["Sponsor", "Budget", "Deliverable", "Approval", "Email thread"],
        "relationships": [["Sponsor", "Budget", "funds"], ["Sponsor", "Deliverable", "entitles"], ["Deliverable", "Approval", "needs"], ["Budget", "Approval", "needs"], ["Email thread", "Sponsor", "mentions"]],
        "roles": ["Event lead", "Finance coordinator", "Sponsorship manager", "Dean (approver)"],
        "workflows": ["Sponsor commitment change", "Budget revision", "Deliverable re-tiering", "Dean approval"],
        "requirements": [
            "Record Acme commitment as Rs 600000 (was Rs 1000000)",
            "Recalculate sponsorship income and budget gap of Rs 400000",
            "Downgrade promotional tier from Title to Gold",
            "Notify Acme and route revised budget for approval",
        ],
        "business_rules": [
            "Budget depends on sponsor commitments",
            "Deliverables depend on sponsor tier",
            "Approvals depend on budget revision",
        ],
        "docs": [
            {"t": "Acme Corporation sponsorship agreement", "src": "sponsor_agreements/acme.pdf", "type": "Document", "score": 0.96, "why": "Defines Rs 10L Title tier and the deliverables tied to it."},
            {"t": "Sponsorship tier policy", "src": "rules/tiers.md", "type": "Business rule", "score": 0.91, "why": "Commitments under Rs 8L qualify for Gold, not Title."},
            {"t": "Budget revision rule", "src": "rules/finance.md", "type": "Business rule", "score": 0.88, "why": "Any change above Rs 1L needs Dean approval."},
        ],
        "tools": [
            {"name": "update_sponsor", "desc": "Update a sponsor record and commitment amount.", "cat": "Sponsors", "scope": "domain", "risk": "high", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"sponsor_id": {"type": "string"}, "new_amount": {"type": "number"}}, "required": ["sponsor_id", "new_amount"]}, "handler": "handlers/update_sponsor.js", "perm": "write"},
            {"name": "update_budget", "desc": "Adjust a budget line and recompute totals.", "cat": "Finance", "scope": "domain", "risk": "high", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"line_id": {"type": "string"}, "delta": {"type": "number"}}, "required": ["line_id", "delta"]}, "handler": "handlers/update_budget.js", "perm": "write"},
            {"name": "flag_promotion", "desc": "Flag deliverables for tier change.", "cat": "Promotion", "scope": "domain", "risk": "medium", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"sponsor_id": {"type": "string"}, "new_tier": {"type": "string"}}, "required": ["sponsor_id", "new_tier"]}, "handler": "handlers/flag_promotion.js", "perm": "write"},
            {"name": "manage_approvals", "desc": "Create or route an approval request.", "cat": "Approvals", "scope": "domain", "risk": "low", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"item": {"type": "string"}, "approver": {"type": "string"}}, "required": ["item", "approver"]}, "handler": "handlers/manage_approvals.js", "perm": "write"},
            {"name": "draft_email", "desc": "Draft an email for review before sending.", "cat": "Communication", "scope": "domain", "risk": "low", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}, "handler": "handlers/draft_email.js", "perm": "draft"},
        ],
        "actions": [
            {"tool": "update_sponsor", "label": "Update Acme commitment", "expected": "Rs 600000", "approval": True, "why": "Changes a financial record"},
            {"tool": "update_budget", "label": "Reduce sponsorship income by Rs 400000", "expected": "Sponsorship line = Rs 600000", "approval": True, "why": "Budget change above Rs 1L"},
            {"tool": "flag_promotion", "label": "Move Acme from Title to Gold tier", "expected": "Tier = Gold", "approval": True, "why": "Alters promised deliverables"},
            {"tool": "draft_email", "label": "Draft confirmation to Acme", "expected": "Draft saved", "fail": "Gmail API timed out (504)"},
            {"tool": "manage_approvals", "label": "Route revised budget to Dean", "expected": "Pending approvals = 1"},
        ],
        "impact": "Budget gap Rs 400000 · 3 deliverables affected · 1 approval required",
        "description": "This project tracks sponsor commitments, budget adjustments, promotional milestones, and finance approvals.",
    },
    "erp": {
        "name": "College ERP",
        "short": "Campus ERP",
        "domain": "Higher-education administration (ERP)",
        "modules": ["Student management", "Faculty management", "Attendance tracking", "Fee management", "Examination management", "Timetable scheduling"],
        "entities": ["Student", "Faculty", "Course", "Attendance", "Fee", "Exam", "Timetable"],
        "relationships": [["Student", "Course", "enrolls"], ["Faculty", "Course", "teaches"], ["Student", "Attendance", "has"], ["Student", "Fee", "owes"], ["Course", "Exam", "has"], ["Course", "Timetable", "scheduled in"]],
        "roles": ["Admin", "Faculty", "Student", "Accounts officer", "Exam controller"],
        "workflows": ["Admission and enrollment", "Daily attendance", "Fee collection", "Exam scheduling", "Timetable generation"],
        "requirements": ["Create and update student records", "Assign faculty to courses", "Mark attendance per session", "Calculate fees with late charges", "Generate conflict-free timetable"],
        "business_rules": ["Attendance depends on enrollment", "Timetable depends on faculty assignment", "Exam eligibility depends on attendance"],
        "docs": [
            {"t": "Academic regulations 2026", "src": "docs/regulations.pdf", "type": "Business rule", "score": 0.93, "why": "75% attendance needed for exam eligibility."},
            {"t": "Fee structure by program", "src": "sheets/fees.xlsx", "type": "Schema", "score": 0.9, "why": "Defines fee heads and late-fee slabs."},
            {"t": "Student table schema", "src": "db/schema.sql", "type": "Schema", "score": 0.85, "why": "Existing columns for student_id, program, year."},
        ],
        "tools": [
            {"name": "create_student", "desc": "Create a student record.", "cat": "Students", "scope": "domain", "risk": "medium", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"name": {"type": "string"}, "program": {"type": "string"}, "year": {"type": "number"}}, "required": ["name", "program", "year"]}, "handler": "handlers/create_student.js", "perm": "write"},
            {"name": "update_student", "desc": "Update fields on a student record.", "cat": "Students", "scope": "domain", "risk": "medium", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"student_id": {"type": "string"}, "fields": {"type": "object"}}, "required": ["student_id", "fields"]}, "handler": "handlers/update_student.js", "perm": "write"},
            {"name": "mark_attendance", "desc": "Mark attendance for a session.", "cat": "Attendance", "scope": "domain", "risk": "low", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"student_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["student_id", "status"]}, "handler": "handlers/mark_attendance.js", "perm": "write"},
            {"name": "calculate_fees", "desc": "Compute fee due including late charges.", "cat": "Fees", "scope": "domain", "risk": "low", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"student_id": {"type": "string"}}, "required": ["student_id"]}, "handler": "handlers/calculate_fees.js", "perm": "read"},
            {"name": "generate_timetable", "desc": "Generate a timetable from constraints.", "cat": "Timetable", "scope": "domain", "risk": "high", "status": "available", "registered": True, "enabled": True, "params": {"type": "object", "properties": {"term": {"type": "string"}, "constraints": {"type": "object"}}, "required": ["term", "constraints"]}, "handler": "handlers/generate_timetable.js", "perm": "write"},
        ],
        "actions": [
            {"tool": "create_student", "label": "Create sample student Aarav Das", "expected": "Student ID = S-1042"},
            {"tool": "assign_faculty", "label": "Assign Dr. Mehta to CS201", "expected": "Faculty = Dr. Mehta"},
            {"tool": "mark_attendance", "label": "Mark Aarav present for CS201", "expected": "Attendance = Present", "fail": "Write conflict on attendance table"},
            {"tool": "calculate_fees", "label": "Calculate Semester 3 fees", "expected": "Rs 84500"},
            {"tool": "generate_timetable", "label": "Generate Semester 3 timetable", "expected": "0 conflicts", "approval": True, "why": "Overwrites the published timetable"},
        ],
        "impact": "6 modules · 7 entities · 5 starter actions",
        "description": "This project manages student lifecycle, faculty assignments, attendance, fee processing, and scheduling for the academic cycle.",
    },
}


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    @property
    def available(self):
        return bool(self.api_key) and genai is not None

    def analyze_requirement(self, requirement: str, project_key: str) -> dict[str, Any]:
        if not self.available:
            return self._fallback(project_key)

        client = genai.Client(api_key=self.api_key)
        prompt = (
            "You are a structured reasoning service for an AI orchestration platform. "
            "Return valid JSON with keys: domain, modules, entities, relationships, workflows, requirements, business_rules, impact, description. "
            "The user requirement is: "
            f"{requirement}"
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            payload = response.text.strip()
            parsed = json.loads(payload)
            return self._normalize(project_key, parsed)
        except Exception:
            return self._fallback(project_key)

    @staticmethod
    def _normalize(project_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        seed = DEFAULT_PROJECTS[project_key]
        name = payload.get("name") or seed["name"]
        short = payload.get("short") or seed["short"]
        domain = payload.get("domain") or seed["domain"]
        return {
            "name": name,
            "short": short,
            "domain": domain,
            "modules": payload.get("modules") or seed["modules"],
            "entities": payload.get("entities") or seed["entities"],
            "relationships": payload.get("relationships") or seed["relationships"],
            "workflows": payload.get("workflows") or seed["workflows"],
            "requirements": payload.get("requirements") or seed["requirements"],
            "business_rules": payload.get("business_rules") or seed["business_rules"],
            "docs": seed.get("docs", []),
            "tools": seed.get("tools", []),
            "actions": seed.get("actions", []),
            "impact": payload.get("impact") or seed["impact"],
            "description": payload.get("description") or seed["description"],
        }

    @staticmethod
    def _fallback(project_key: str) -> dict[str, Any]:
        return DEFAULT_PROJECTS[project_key].copy()


class DatabaseSchemaService:
    @staticmethod
    def introspect() -> dict[str, Any]:
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            payload = []
            for table in tables:
                columns = connection.introspection.get_table_description(cursor, table)
                primary_keys = connection.introspection.get_primary_key_column(cursor, table)
                payload.append({
                    "table": table,
                    "columns": [
                        {
                            "name": c.name,
                            "type_code": c.type_code,
                            "display_size": c.display_size,
                            "internal_size": c.internal_size,
                            "precision": c.precision,
                            "scale": c.scale,
                            "null_ok": c.null_ok,
                        }
                        for c in columns
                    ],
                    "primary_keys": primary_keys,
                    "foreign_keys": [],
                })
        return {"tables": payload, "generated_at": datetime.utcnow().isoformat()}


class ProjectService:
    @staticmethod
    def determine_project_key(requirement: str) -> str:
        text = (requirement or "").lower()
        if any(word in text for word in ["sponsor", "budget", "deliverable", "festival", "event", "promotions", "acme"]):
            return "event"
        if any(word in text for word in ["student", "faculty", "attendance", "fee", "timetable", "exam", "erp", "campus"]):
            return "erp"
        return "event"

    @classmethod
    def analyze_requirement(cls, requirement: str) -> dict[str, Any]:
        project_key = cls.determine_project_key(requirement)
        generated = GeminiService().analyze_requirement(requirement, project_key)
        return {
            "project_key": project_key,
            "project": generated,
            "schema": DatabaseSchemaService.introspect(),
            "capabilities": [
                {"name": "Read sponsor detail", "classification": "Available" if project_key == "event" else "Adaptable"},
                {"name": "Update budget", "classification": "Available" if project_key == "event" else "Adaptable"},
                {"name": "Route approval", "classification": "Available"},
            ],
        }

    @staticmethod
    def build_workflow(project_data: dict[str, Any]) -> list[dict[str, Any]]:
        actions = project_data.get("actions", [])
        return [{
            "tool": item["tool"],
            "label": item["label"],
            "expected": item.get("expected"),
            "approval": item.get("approval", False),
            "why": item.get("why", "Required for the workflow"),
        } for item in actions]

    @staticmethod
    def serialize_project(project_obj) -> dict[str, Any]:
        return {
            "id": str(project_obj.id),
            "name": project_obj.name,
            "short": project_obj.short_name or project_obj.name,
            "domain": project_obj.domain,
            "description": project_obj.description,
            "modules": project_obj.modules,
            "entities": project_obj.entities,
            "relationships": project_obj.relationships,
            "workflows": project_obj.workflows,
            "requirements": project_obj.requirements,
            "business_rules": project_obj.business_rules,
            "impact": project_obj.metadata.get("impact", "No impact recorded."),
            "tools": [
                {
                    "name": tool.tool_name,
                    "desc": tool.description,
                    "cat": tool.tool_name,
                    "scope": "domain",
                    "risk": tool.risk_level,
                    "status": tool.status,
                    "registered": True,
                    "enabled": True,
                    "params": tool.input_schema,
                    "handler": tool.handler_config.get("path", "handlers/default.js"),
                    "perm": tool.permissions[0] if tool.permissions else "write",
                }
                for tool in project_obj.tools.all()
            ],
            "actions": project_obj.metadata.get("actions", []),
            "docs": project_obj.metadata.get("docs", []),
        }

    @staticmethod
    def ensure_project_tool_registry(project, project_data: dict[str, Any]) -> list[dict[str, Any]]:
        tool_definitions = []
        for tool in project_data.get("tools", []):
            safe_template = SAFE_TOOL_TEMPLATES.get(tool["name"], {})
            if safe_template:
                tool["handler"] = "core.tool_templates.execute_safe_template"
                tool["template"] = safe_template["name"]
            project_tool, _ = project.tools.update_or_create(
                tool_name=tool["name"],
                defaults={
                    "description": tool.get("desc", tool.get("description", "")),
                    "input_schema": tool.get("params", {}),
                    "output_schema": safe_template.get("output_schema", {"type": "object"}),
                    "handler_type": "template",
                    "handler_config": {
                        "path": tool.get("handler", "core.tool_templates.execute_safe_template"),
                        "template": safe_template.get("name", tool["name"]),
                    },
                    "permissions": tool.get("perm") and [tool["perm"]] or safe_template.get("permissions", ["write"]),
                    "risk_level": tool.get("risk", safe_template.get("risk_level", "low")),
                    "validation_rules": [safe_template.get("verification", "Template validation")],
                    "verification_rules": [safe_template.get("verification", "Template validation")],
                    "idempotency_required": True,
                    "status": tool.get("status", "Active"),
                },
            )
            tool_definitions.append({
                "tool_id": str(project_tool.id),
                "name": project_tool.tool_name,
                "status": project_tool.status,
                "template": project_tool.handler_config.get("template", project_tool.tool_name),
            })
        return tool_definitions

    @staticmethod
    def execute_project_steps(project, workflow: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        default_payloads = {
            "update_sponsor": {"sponsor_id": "acme", "new_amount": 600000, "sponsor_name": "Acme Corporation"},
            "update_budget": {"line_id": "sponsorship_income", "delta": -400000, "label": "Sponsorship income"},
            "flag_promotion": {"sponsor_id": "acme", "new_tier": "Gold"},
            "manage_approvals": {"item": "budget_revision", "approver": "Dean", "notes": "Budget revised after sponsor change"},
            "draft_email": {"to": "acme@corp.example", "subject": "Budget revision", "body": "We have updated the commitment and budget."},
            "create_student": {"student_id": "S-1042", "name": "Aarav Das", "program": "BTech", "year": 3},
            "mark_attendance": {"student_id": "S-1042", "status": "Present", "course": "CS201"},
            "calculate_fees": {"student_id": "S-1042", "base_amount": 50000, "late_fee": 34500},
            "generate_timetable": {"term": "Semester 3", "constraints": {"conflict_count": 0}},
        }

        for step in workflow:
            tool_name = step.get("tool")
            payload = (step.get("input") or {"tool": tool_name})
            if tool_name in default_payloads and not payload.get("tool"):
                payload = default_payloads[tool_name]
            if not payload and tool_name in default_payloads:
                payload = default_payloads[tool_name]
            try:
                result = execute_safe_template(project, tool_name, payload)
                log = create_tool_execution_log(project, tool_name, payload, result)
                results.append({"tool": tool_name, "status": "success", "result": result, "log_id": str(log.id)})
            except Exception as exc:  # pragma: no cover - defensive fallback
                results.append({"tool": tool_name, "status": "failed", "error": str(exc)})
        return results
