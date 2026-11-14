from django.test import TestCase

from .models import Project
from .services import ProjectService
from .tool_templates import execute_safe_template


class ProjectServiceTests(TestCase):
    def test_determine_project_key_for_event_requirement(self):
        key = ProjectService.determine_project_key("Acme reduced sponsorship commitment and budget needs approval")
        self.assertEqual(key, "event")

    def test_determine_project_key_for_erp_requirement(self):
        key = ProjectService.determine_project_key("Create student attendance and timetable system for the campus")
        self.assertEqual(key, "erp")

    def test_analyze_requirement_returns_project_shape(self):
        analysis = ProjectService.analyze_requirement("Manage a college technical fest with sponsor tracking and budget approval")
        self.assertIn("project", analysis)
        self.assertIn("schema", analysis)
        self.assertIn("requirements", analysis["project"])
        self.assertIn("modules", analysis["project"])
        self.assertIn("impact", analysis["project"])

    def test_safe_tool_template_updates_project_state(self):
        project = Project.objects.create(
            name="Test Project",
            short_name="Test",
            domain="Event Ops",
            description="Demo",
            requirements=["Update sponsor commitment"],
            modules=["Sponsors"],
            entities=["Sponsor"],
            relationships=[],
            workflows=["Sponsor update"],
            business_rules=[],
            available_operations=[],
            permissions=[],
            metadata={"impact": "Low"},
        )
        result = execute_safe_template(project, "update_sponsor", {"sponsor_id": "acme", "new_amount": 600000, "sponsor_name": "Acme"})
        self.assertEqual(result["status"], "updated")
        state = project.state_records.get(entity="sponsor", external_id="acme")
        self.assertEqual(state.payload["current_amount"], 600000.0)
