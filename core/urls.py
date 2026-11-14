from django.urls import path

from .views import (
    ApprovalDecisionView,
    ProjectListView,
    RequirementAnalyzeView,
    ToolRegistryView,
    WorkflowRunView,
)

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="projects"),
    path("requirements/analyze/", RequirementAnalyzeView.as_view(), name="requirements-analyze"),
    path("workflows/run/", WorkflowRunView.as_view(), name="workflows-run"),
    path("approvals/<uuid:approval_id>/decision/", ApprovalDecisionView.as_view(), name="approvals-decision"),
    path("tools/", ToolRegistryView.as_view(), name="tool-registry"),
]
