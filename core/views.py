from pathlib import Path

from django.http import FileResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ApprovalDecision, Project, ProjectTool, WorkflowExecution
from .services import ProjectService
from .tool_templates import SAFE_TOOL_TEMPLATES

BASE_DIR = Path(__file__).resolve().parent.parent


def home(request):
    html_file = BASE_DIR / "index.html"
    return FileResponse(html_file.open("rb"), content_type="text/html")


def serve_asset(request, filename):
    file_path = BASE_DIR / filename
    if not file_path.exists():
        return JsonResponse({"detail": "Asset not found"}, status=404)
    return FileResponse(file_path.open("rb"), content_type="text/plain")


class ProjectListView(APIView):
    def get(self, request):
        projects = Project.objects.all()
        return Response([{"id": str(project.id), "name": project.name, "domain": project.domain} for project in projects])


class RequirementAnalyzeView(APIView):
    def post(self, request):
        requirement = (request.data.get("requirement") or request.data.get("prompt") or "").strip()
        if not requirement:
            return Response({"detail": "Requirement is required."}, status=status.HTTP_400_BAD_REQUEST)

        analysis = ProjectService.analyze_requirement(requirement)
        project_key = analysis["project_key"]
        project_data = analysis["project"]

        project = None
        project_id = request.data.get("project_id")
        if project_id:
            project = Project.objects.filter(id=project_id).first()
        if project is None:
            project = Project.objects.create(
                name=project_data["name"],
                short_name=project_data["short"],
                domain=project_data["domain"],
                description=project_data.get("description", ""),
                requirements=project_data.get("requirements", []),
                modules=project_data.get("modules", []),
                entities=project_data.get("entities", []),
                relationships=project_data.get("relationships", []),
                workflows=project_data.get("workflows", []),
                business_rules=project_data.get("business_rules", []),
                available_operations=[],
                permissions=[],
                metadata={
                    "project_key": project_key,
                    "impact": project_data.get("impact", ""),
                    "actions": project_data.get("actions", []),
                    "docs": project_data.get("docs", []),
                    "raw_requirement": requirement,
                },
            )
        else:
            project.name = project_data["name"]
            project.short_name = project_data["short"]
            project.domain = project_data["domain"]
            project.description = project_data.get("description", "")
            project.requirements = project_data.get("requirements", [])
            project.modules = project_data.get("modules", [])
            project.entities = project_data.get("entities", [])
            project.relationships = project_data.get("relationships", [])
            project.workflows = project_data.get("workflows", [])
            project.business_rules = project_data.get("business_rules", [])
            project.metadata = {
                "project_key": project_key,
                "impact": project_data.get("impact", ""),
                "actions": project_data.get("actions", []),
                "docs": project_data.get("docs", []),
                "raw_requirement": requirement,
            }
            project.save()

        ProjectService.ensure_project_tool_registry(project, project_data)

        return Response({
            "project": {
                "id": str(project.id),
                **project_data,
            },
            "schema": analysis["schema"],
            "capabilities": analysis["capabilities"],
            "templates": [
                {"name": name, "risk_level": template["risk_level"], "permissions": template["permissions"]}
                for name, template in SAFE_TOOL_TEMPLATES.items()
            ],
        })


class WorkflowRunView(APIView):
    def post(self, request):
        requirement = (request.data.get("requirement") or request.data.get("prompt") or "").strip()
        project_id = request.data.get("project_id")
        if not requirement:
            return Response({"detail": "Requirement is required."}, status=status.HTTP_400_BAD_REQUEST)

        project = Project.objects.filter(id=project_id).first() if project_id else Project.objects.order_by("-updated_at").first()
        if project is None:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        project_data = {
            "name": project.name,
            "domain": project.domain,
            "short": project.short_name or project.name,
            "requirements": project.requirements,
            "modules": project.modules,
            "entities": project.entities,
            "relationships": project.relationships,
            "workflows": project.workflows,
            "business_rules": project.business_rules,
            "actions": project.metadata.get("actions", []),
            "impact": project.metadata.get("impact", ""),
            "docs": project.metadata.get("docs", []),
            "tools": [
                {
                    "name": tool.tool_name,
                    "desc": tool.description,
                    "risk": tool.risk_level,
                    "status": tool.status,
                    "perm": tool.permissions[0] if tool.permissions else "write",
                    "handler": tool.handler_config.get("path", "handlers/default.js"),
                    "params": tool.input_schema,
                }
                for tool in project.tools.all()
            ],
        }

        workflow = ProjectService.build_workflow(project_data)
        execution = WorkflowExecution.objects.create(
            project=project,
            requirement=requirement,
            plan=workflow,
            status="running",
            approval_required=any(item.get("approval") for item in workflow),
            result={"steps": workflow, "verified": [], "failed": [], "skipped": []},
        )

        execution_results = ProjectService.execute_project_steps(project, workflow)
        execution.status = "done" if all(item.get("status") == "success" for item in execution_results) else "partial"
        execution.result = {
            "steps": workflow,
            "executed": execution_results,
            "verified": [item for item in execution_results if item.get("status") == "success"],
            "failed": [item for item in execution_results if item.get("status") == "failed"],
            "skipped": [],
        }
        execution.save(update_fields=["status", "result", "updated_at"])

        return Response({
            "execution_id": str(execution.id),
            "status": execution.status,
            "plan": workflow,
            "results": execution_results,
            "project": {"id": str(project.id), "name": project.name, "short": project.short_name or project.name, "domain": project.domain},
        })


class ApprovalDecisionView(APIView):
    def post(self, request, approval_id):
        execution = WorkflowExecution.objects.filter(id=approval_id).first()
        if execution is None:
            return Response({"detail": "Execution not found."}, status=status.HTTP_404_NOT_FOUND)

        approved = request.data.get("approved", False)
        action_label = request.data.get("action_label") or "Approval decision"
        tool_name = request.data.get("tool_name") or "unknown_tool"
        notes = request.data.get("notes", "")

        approval = ApprovalDecision.objects.create(
            execution=execution,
            action_label=action_label,
            tool_name=tool_name,
            approved=bool(approved),
            notes=notes,
        )
        execution.status = "done" if approved else "rejected"
        execution.result["approved"] = bool(approved)
        execution.result["last_decision"] = {"action_label": action_label, "tool_name": tool_name, "approved": bool(approved)}
        execution.save(update_fields=["status", "result", "updated_at"])
        return Response({"status": execution.status, "approval": {"id": str(approval.id), "approved": bool(approved)}})


class ToolRegistryView(APIView):
    def get(self, request):
        project_id = request.query_params.get("project_id")
        queryset = ProjectTool.objects.all()
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return Response([
            {
                "id": str(tool.id),
                "name": tool.tool_name,
                "desc": tool.description,
                "risk": tool.risk_level,
                "status": tool.status,
                "perm": tool.permissions[0] if tool.permissions else "write",
                "params": tool.input_schema,
            }
            for tool in queryset
        ])

    def post(self, request):
        project_id = request.data.get("project_id")
        if not project_id:
            return Response({"detail": "project_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        project = Project.objects.filter(id=project_id).first()
        if project is None:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        template_name = request.data.get("template_name") or request.data.get("name")
        if template_name and template_name not in SAFE_TOOL_TEMPLATES:
            return Response({"detail": "Only approved, safe templates are allowed. See SAFE_TOOL_TEMPLATES."}, status=status.HTTP_400_BAD_REQUEST)

        tool_name = request.data.get("name") or template_name or "new_tool"
        template = SAFE_TOOL_TEMPLATES.get(template_name or tool_name, {})
        tool = ProjectTool.objects.create(
            project=project,
            tool_name=tool_name,
            description=request.data.get("desc", template.get("description", "")),
            input_schema=request.data.get("params", template.get("input_schema", {"type": "object", "properties": {}})),
            output_schema=template.get("output_schema", {"type": "object"}),
            handler_type="template",
            handler_config={
                "path": request.data.get("handler", "core.tool_templates.execute_safe_template"),
                "template": template_name or tool_name,
            },
            permissions=[request.data.get("perm", template.get("permissions", ["write"])[0])],
            risk_level=request.data.get("risk", template.get("risk_level", "low")),
            validation_rules=[template.get("verification", "Template validation")],
            verification_rules=[template.get("verification", "Template validation")],
            idempotency_required=True,
            status="Active",
        )

        return Response({"id": str(tool.id), "name": tool.tool_name, "status": tool.status, "template": template_name or tool_name}, status=status.HTTP_201_CREATED)
