"""Shared validation and persistence for imported Playwright recordings."""

from django.db import transaction

from .models import TestScript
from .operation_logger import log_operation
from .script_security import ScriptSecurityError, analyze_script


def analyze_recorded_script(content):
    """Validate an imported recording and return its analysis metadata."""
    if not isinstance(content, str):
        raise ScriptSecurityError('脚本内容格式无效')
    if not content.strip():
        raise ScriptSecurityError('请上传或粘贴Python脚本')
    return analyze_script(content)


def _request_bool(value, default=False):
    """Parse JSON and multipart form boolean values consistently."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def import_recorded_script(project, user, content, *, name='', start_url='',
                           browser='chromium', device='', save_storage=False,
                           expected_content_hash=''):
    """Validate and persist a recording for an already-authorized project.

    The expected hash is supplied by MCP confirmation to bind execution to the
    exact source reviewed during preview.
    """
    analysis = analyze_recorded_script(content)
    if expected_content_hash and analysis['content_hash'] != expected_content_hash:
        raise ScriptSecurityError('待确认的脚本内容与预览不一致')

    clean_name = str(name or 'testhub_recorded.py').strip()[:200]
    with transaction.atomic():
        script = TestScript.objects.create(
            project=project,
            name=clean_name or 'testhub_recorded.py',
            script_type='CODE',
            content=content,
            language='python',
            framework='playwright',
            source='recorded',
            start_url=str(start_url or analysis.get('start_url') or '')[:500],
            recording_config={
                'browser': browser or 'chromium',
                'device': device or '',
                'save_storage': _request_bool(save_storage, False),
            },
            analysis={key: value for key, value in analysis.items()
                      if key != 'normalized_content'},
        )
        log_operation('create', 'script', script.id, script.name, user)
    return script, analysis
