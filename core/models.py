import uuid

from django.db import models


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=120, blank=True)
    domain = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    requirements = models.JSONField(default=list)
    modules = models.JSONField(default=list)
    entities = models.JSONField(default=list)
    relationships = models.JSONField(default=list)
    workflows = models.JSONField(default=list)
    business_rules = models.JSONField(default=list)
    available_operations = models.JSONField(default=list)
    permissions = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class ProjectTool(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Validating", "Validating"),
        ("Approved", "Approved"),
        ("Active", "Active"),
        ("Disabled", "Disabled"),
        ("Rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tools")
    tool_name = models.CharField(max_length=150)
    description = models.TextField()
    input_schema = models.JSONField(default=dict)
    output_schema = models.JSONField(default=dict)
    handler_type = models.CharField(max_length=80, default="template")
    handler_config = models.JSONField(default=dict)
    permissions = models.JSONField(default=list)
    risk_level = models.CharField(max_length=20, default="low")
    validation_rules = models.JSONField(default=list)
    verification_rules = models.JSONField(default=list)
    idempotency_required = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tool_name"]

    def __str__(self):
        return self.tool_name


class RequirementAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="analyses")
    raw_requirement = models.TextField()
    summary = models.TextField(blank=True)
    domain = models.CharField(max_length=200)
    modules = models.JSONField(default=list)
    entities = models.JSONField(default=list)
    relationships = models.JSONField(default=list)
    workflows = models.JSONField(default=list)
    requirements = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class WorkflowExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="executions")
    requirement = models.TextField()
    plan = models.JSONField(default=list)
    status = models.CharField(max_length=30, default="pending")
    result = models.JSONField(default=dict)
    approval_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProjectState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="state_records")
    entity = models.CharField(max_length=120)
    external_id = models.CharField(max_length=200)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "entity", "external_id")]


class ProjectApproval(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="approvals")
    item = models.CharField(max_length=200)
    approver = models.CharField(max_length=120)
    status = models.CharField(max_length=20, default="pending")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProjectNotification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=40, default="email")
    recipient = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)


class ToolExecutionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tool_logs")
    tool_name = models.CharField(max_length=150)
    request_payload = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="success")
    created_at = models.DateTimeField(auto_now_add=True)


class ApprovalDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name="approvals")
    action_label = models.CharField(max_length=200)
    tool_name = models.CharField(max_length=120)
    approved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
