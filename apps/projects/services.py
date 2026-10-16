from django.db import transaction
from django.utils import timezone

from .models import Project, ProjectMember


MODULE_LABELS = {
    'ai_generation': 'AI用例生成',
    'ai_testing': 'AI智能测试',
    'api': 'API测试',
    'ui': 'UI自动化',
    'app': 'APP自动化',
    'perf': '性能测试',
}

MODULE_MODELS = {}


def _module_model(module):
    if module not in MODULE_MODELS:
        from apps.api_testing.models import ApiProject
        from apps.ui_automation.models import UiProject
        from apps.app_automation.models import AppProject
        from apps.perf_testing.models import PerfProject
        MODULE_MODELS.update(api=ApiProject, ui=UiProject, app=AppProject, perf=PerfProject)
    return MODULE_MODELS.get(module)


def _status_for_module(status, model):
    choices = {key for key, _ in model.STATUS_CHOICES}
    if status in choices:
        return status
    return 'IN_PROGRESS' if 'IN_PROGRESS' in choices else next(iter(choices))


def _module_config(module, config, project):
    config = dict(config or {})
    values = {
        'name': project.name,
        'description': project.description,
        'status': _status_for_module(project.status, _module_model(module)),
    }
    allowed = {
        'api': ('project_type', 'start_date', 'end_date'),
        'ui': ('base_url', 'start_date', 'end_date'),
        'app': ('start_date', 'end_date'),
        'perf': ('default_env',),
    }
    values.update({key: config[key] for key in allowed.get(module, ()) if key in config})
    if module == 'api':
        values.setdefault('project_type', 'HTTP')
    if module == 'ui':
        values.setdefault('base_url', 'http://localhost')
    return values


def sync_module_members(project, module_project):
    member_ids = ProjectMember.objects.filter(project=project).values_list('user_id', flat=True)
    module_project.members.set(member_ids)


def sync_project_members_from_module(module_project):
    project = module_project.workspace_project
    if not project:
        return
    ProjectMember.objects.filter(project=project).exclude(user_id=project.owner_id).delete()
    ProjectMember.objects.bulk_create([
        ProjectMember(project=project, user_id=user_id, role='tester')
        for user_id in module_project.members.values_list('id', flat=True)
        if user_id != project.owner_id
    ], ignore_conflicts=True)


def sync_workspace_project_from_module(module_project, module):
    project = module_project.workspace_project
    if not project:
        return
    project.name = module_project.name
    project.description = module_project.description
    status_map = {'NOT_STARTED': 'active', 'IN_PROGRESS': 'active', 'COMPLETED': 'completed'}
    project.status = status_map.get(module_project.status, project.status)
    if module not in (project.modules or []):
        project.modules = list(project.modules or []) + [module]
    project.save(update_fields=['name', 'description', 'status', 'modules', 'updated_at'])


def sync_all_module_members(project):
    for module in ('api', 'ui', 'app', 'perf'):
        model = _module_model(module)
        module_project = model.all_objects.filter(workspace_project=project).first()
        if module_project:
            sync_module_members(project, module_project)


@transaction.atomic
def ensure_workspace_project_for_module(module_project, module, user):
    """Attach a module-created project to the common project center."""
    if module_project.workspace_project_id:
        return module_project.workspace_project
    project = Project.objects.create(
        name=module_project.name,
        description=module_project.description,
        status='active',
        owner=module_project.owner or user,
        modules=[module],
    )
    ProjectMember.objects.bulk_create([
        ProjectMember(project=project, user_id=user_id, role='tester')
        for user_id in module_project.members.values_list('id', flat=True)
        if user_id != project.owner_id
    ], ignore_conflicts=True)
    module_project.workspace_project = project
    module_project.save(update_fields=['workspace_project'])
    sync_module_members(project, module_project)
    return project


@transaction.atomic
def create_unified_project(*, user, name, description='', status='active', modules=None,
                           member_ids=None, module_configs=None):
    modules = list(dict.fromkeys(modules or []))
    project = Project.objects.create(
        name=name,
        description=description,
        status=status,
        owner=user,
        modules=modules,
    )
    member_ids = set(member_ids or []) - {user.id}
    ProjectMember.objects.bulk_create([
        ProjectMember(project=project, user_id=user_id, role='tester')
        for user_id in member_ids
    ], ignore_conflicts=True)
    for module in modules:
        model = _module_model(module)
        if model is None:
            continue
        values = _module_config(module, (module_configs or {}).get(module), project)
        module_project = model.objects.create(owner=user, workspace_project=project, **values)
        sync_module_members(project, module_project)
    return project


@transaction.atomic
def update_unified_project(project, *, user, name=None, description=None, status=None,
                           modules=None, member_ids=None, module_configs=None):
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if status is not None:
        project.status = status
    if modules is not None:
        project.modules = list(dict.fromkeys(modules))
    project.save()
    if member_ids is not None:
        ProjectMember.objects.filter(project=project).exclude(user_id=project.owner_id).delete()
        ProjectMember.objects.bulk_create([
            ProjectMember(project=project, user_id=user_id, role='tester')
            for user_id in set(member_ids) - {project.owner_id}
        ], ignore_conflicts=True)
    for module in project.modules:
        model = _module_model(module)
        if model is None:
            continue
        module_project = model.all_objects.filter(workspace_project=project).first()
        config = (module_configs or {}).get(module)
        if module_project is None:
            module_project = model.objects.create(
                owner=project.owner,
                workspace_project=project,
                **_module_config(module, config, project),
            )
        else:
            module_project.is_deleted = False
            module_project.deleted_at = None
            module_project.deleted_by = None
            module_project.name = project.name
            module_project.description = project.description
            module_project.status = _status_for_module(project.status, model)
            if config:
                for key, value in _module_config(module, config, project).items():
                    if key == 'status':
                        module_project.status = value
                        continue
                    if key in ('name', 'description'):
                        continue
                    if value not in ('', None):
                        setattr(module_project, key, value)
            module_project.save()
        sync_module_members(project, module_project)
    for module in ('api', 'ui', 'app', 'perf'):
        if module in project.modules:
            continue
        model = _module_model(module)
        module_project = model.all_objects.filter(workspace_project=project).first()
        if module_project and not module_project.is_deleted:
            module_project.is_deleted = True
            module_project.deleted_at = timezone.now()
            module_project.deleted_by = user
            module_project.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])
    return project


def soft_delete_module_project(instance, user):
    instance.is_deleted = True
    instance.deleted_at = timezone.now()
    instance.deleted_by = user
    instance.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])


def sync_legacy_projects(user=None):
    """Make pre-center module projects visible in the center without a data migration."""
    from apps.api_testing.models import ApiProject
    from apps.ui_automation.models import UiProject
    from apps.app_automation.models import AppProject
    from apps.perf_testing.models import PerfProject
    for module, model in (('api', ApiProject), ('ui', UiProject), ('app', AppProject), ('perf', PerfProject)):
        qs = model.all_objects.filter(workspace_project__isnull=True)
        if user is not None:
            qs = qs.filter(owner=user)
        for module_project in qs.iterator():
            ensure_workspace_project_for_module(module_project, module, module_project.owner)
