import os
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.ui_automation.models import StorageState, TestExecution, TestScript, UiProject
from apps.ui_automation.serializers import TestCaseStepSerializer
from apps.ui_automation.script_runner import execute_script, get_playwright_browsers_path
from apps.ui_automation.script_security import MAX_SCRIPT_BYTES, ScriptSecurityError, analyze_script


class RecordedScriptSecurityTests(SimpleTestCase):
    def test_codegen_script_is_normalized_for_runtime_configuration(self):
        content = '''from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com/login")
    page.get_by_role("button", name="Sign in").click()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
'''

        result = analyze_script(content)

        self.assertEqual(result['framework'], 'playwright')
        self.assertEqual(result['locator_count'], 1)
        self.assertEqual(result['start_url'], 'https://example.com/login')
        self.assertIn("os.environ.get('HEADLESS', '0')", result['normalized_content'])
        self.assertIn("os.environ.get('TESTHUB_BASE_URL') or 'https://example.com/login'", result['normalized_content'])

    def test_dangerous_import_is_rejected(self):
        with self.assertRaisesRegex(ScriptSecurityError, '不允许导入 subprocess'):
            analyze_script('import subprocess\nsubprocess.run(["whoami"])')

    def test_dangerous_call_is_rejected(self):
        with self.assertRaisesRegex(ScriptSecurityError, '禁止调用 open'):
            analyze_script('from playwright.sync_api import sync_playwright\nopen("secret.txt")')

    def test_os_and_reflection_escape_hatches_are_rejected(self):
        with self.assertRaisesRegex(ScriptSecurityError, '禁止访问 os.remove'):
            analyze_script('import os\nos.remove("/tmp/testhub-secret")')
        with self.assertRaisesRegex(ScriptSecurityError, '禁止调用 getattr'):
            analyze_script('import os\ngetattr(os, "system")("whoami")')
        with self.assertRaisesRegex(ScriptSecurityError, '不允许为 os 使用别名'):
            analyze_script('import os as runtime\nruntime.system("whoami")')
        with self.assertRaisesRegex(ScriptSecurityError, '不允许从 os 导入成员'):
            analyze_script('from os import system\nsystem("whoami")')

    def test_script_size_is_limited(self):
        with self.assertRaisesRegex(ScriptSecurityError, '不能超过2MB'):
            analyze_script('x = "' + ('a' * MAX_SCRIPT_BYTES) + '"')


class RecordedScriptRunnerTests(SimpleTestCase):
    def test_preserves_configured_playwright_browser_cache(self):
        with patch.dict(os.environ, {'PLAYWRIGHT_BROWSERS_PATH': '/custom/playwright-cache'}):
            self.assertEqual(get_playwright_browsers_path(), '/custom/playwright-cache')

    def test_empty_base_url_override_preserves_codegen_url(self):
        source = '''from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    browser.close()
'''

        normalized = analyze_script(source)['normalized_content']

        self.assertIn("os.environ.get('TESTHUB_BASE_URL') or 'https://example.com'", normalized)

    def test_preflight_reports_the_four_recording_risk_categories(self):
        content = '''from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    page.get_by_role("button").click()
    page.get_by_role("button", name="菜单").click()
    page.screenshot(path="/Users/tester/output.png")
'''

        result = analyze_script(content)

        categories = {item['category'] for item in result['diagnostics']}
        self.assertTrue({
            'locator_ambiguity', 'wait_state', 'toggle_state', 'environment_coupling'
        }.issubset(categories))

    def test_preflight_does_not_warn_for_explicit_first_role_locator(self):
        result = analyze_script('page.get_by_role("button").first.click()')

        self.assertNotIn('locator_ambiguity', {item['category'] for item in result['diagnostics']})

    def test_replay_normalizer_adds_runtime_toggle_and_path_adapters(self):
        result = analyze_script('''from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.get_by_role("button", name="菜单").click()
    page.screenshot(path="/Users/tester/output.png")
    browser.close()
''')

        self.assertIn('_testhub_toggle_click', result['normalized_content'])
        self.assertIn('TESTHUB_WORKDIR', result['normalized_content'])
        self.assertEqual({item['category'] for item in result['optimizations']}, {'toggle_state', 'environment_coupling'})


class StorageStateApiTests(TestCase):
    """覆盖登录态上传、下载和步骤参数校验的接口契约。"""

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username='storage-state-user', password='password')
        self.project = UiProject.objects.create(
            name='Storage state project', base_url='https://example.com', owner=self.user
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_upload_and_download_storage_state(self):
        # 使用最小合法 storage_state 验证文件大小记录和下载内容保持一致。
        content = b'{"cookies": [], "origins": []}'
        response = self.client.post(
            '/api/ui-automation/storage-states/',
            {
                'project': self.project.id,
                'name': '登录态一',
                'file': SimpleUploadedFile('storage_state.json', content, content_type='application/json'),
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, 201, response.data)
        state = StorageState.objects.get(pk=response.data['id'])
        self.assertEqual(state.file_size, len(content))
        download = self.client.get(f'/api/ui-automation/storage-states/{state.id}/download/')
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b''.join(download.streaming_content), content)

    def test_storage_state_step_requires_operation_and_target(self):
        # 步骤参数缺失时应在序列化层阻止无效保存或切换动作。
        missing_operation = TestCaseStepSerializer(data={
            'step_number': 1, 'action_type': 'storageState', 'action_params': {}
        })
        self.assertFalse(missing_operation.is_valid())
        self.assertIn('action_params', missing_operation.errors)

        missing_target = TestCaseStepSerializer(data={
            'step_number': 1, 'action_type': 'storageState', 'action_params': {'operation': 'switch'}
        })
        self.assertFalse(missing_target.is_valid())
        self.assertIn('non_field_errors', missing_target.errors)


class RecordedScriptApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username='recording-user', password='password')
        self.project = UiProject.objects.create(
            name='Recording project',
            base_url='https://example.com',
            owner=self.user,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_zero_exit_without_browser_launch_is_failed_and_logs_environment(self):
        execution = TestExecution.objects.create(
            project=self.project,
            execution_type='recorded_script',
            status='PENDING',
            engine='playwright',
            browser='chromium',
            headless=True,
        )

        with patch('apps.ui_automation.script_runner.close_old_connections'):
            execute_script(execution.id, 'print("script exited without launching a browser")')

        execution.refresh_from_db()
        self.assertEqual(execution.status, 'FAILED')
        self.assertIn('执行引擎=Playwright，浏览器=Chromium，模式=无头', execution.execution_logs)
        self.assertIn('执行结果：failed', execution.execution_logs)
        self.assertIn(f'执行耗时：{execution.duration:.2f}秒', execution.execution_logs)
        self.assertIn('未实际启动Playwright浏览器', execution.execution_logs)

    def test_replay_logs_automatic_checks_and_path_rewrite(self):
        execution = TestExecution.objects.create(
            project=self.project,
            execution_type='recorded_script',
            status='PENDING',
            engine='playwright',
            browser='chromium',
            headless=True,
        )
        content = '''from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    page.get_by_role("button").click()
    page.screenshot(path="/Users/tester/output.png")
    browser.close()
'''

        with patch('apps.ui_automation.script_runner.close_old_connections'):
            execute_script(execution.id, content)

        execution.refresh_from_db()
        self.assertNotIn('回放自动检查与处理', execution.execution_logs)
        self.assertNotIn('运行时适配已启用', execution.execution_logs)
        self.assertIn('执行结果：failed', execution.execution_logs)
        self.assertIn('排查建议：', execution.execution_logs)
        self.assertIn('TESTHUB_WORKDIR', analyze_script(content)['normalized_content'])

    def test_actual_headless_chromium_launch_is_recorded_as_passed(self):
        browser_cache = Path(get_playwright_browsers_path())
        if not any(browser_cache.glob('chromium-*')):
            self.skipTest('本机未安装Playwright Chromium')
        execution = TestExecution.objects.create(
            project=self.project,
            execution_type='recorded_script',
            status='PENDING',
            engine='playwright',
            browser='chromium',
            headless=True,
        )
        content = '''from playwright.sync_api import sync_playwright
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    browser.close()
'''

        with patch('apps.ui_automation.script_runner.close_old_connections'):
            execute_script(execution.id, content)

        execution.refresh_from_db()
        self.assertEqual(execution.status, 'SUCCESS', execution.execution_logs)
        self.assertNotIn('Playwright browser launch succeeded', execution.execution_logs)
        self.assertNotIn('Chromium浏览器启动已确认', execution.execution_logs)
        self.assertNotIn('回放自动检查与处理', execution.execution_logs)
        self.assertNotIn('运行时适配已启用', execution.execution_logs)
        self.assertIn('执行结果：passed', execution.execution_logs)
        self.assertGreater(execution.duration, 0)

    def test_recording_command_is_generated_for_chromium(self):
        response = self.client.post(
            '/api/ui-automation/test-scripts/recording-command/',
            {'start_url': 'https://example.com/login', 'browser': 'chromium'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('playwright codegen', response.data['record_command'])
        self.assertIn('--browser=chromium', response.data['record_command'])

    def test_preflight_api_returns_hash_and_risk_diagnostics(self):
        response = self.client.post(
            '/api/ui-automation/test-scripts/preflight/',
            {'content': 'page.get_by_role("button").click()'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['content_hash']), 64)
        self.assertIn('locator_ambiguity', {item['category'] for item in response.data['diagnostics']})

    def test_import_persists_analyzed_recording(self):
        content = 'from playwright.sync_api import sync_playwright\n\nwith sync_playwright() as p:\n    browser = p.chromium.launch()\n    page = browser.new_page()\n    page.goto("https://example.com")\n    browser.close()\n'

        response = self.client.post(
            '/api/ui-automation/test-scripts/import/',
            {'project': self.project.id, 'content': content, 'name': 'login.py', 'browser': 'chromium'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        script = TestScript.objects.get(pk=response.data['id'])
        self.assertEqual(script.source, 'recorded')
        self.assertEqual(script.analysis['locator_count'], 0)
        self.assertEqual(script.start_url, 'https://example.com')

    @patch('apps.ui_automation.views.start_script_execution')
    def test_unsaved_replay_creates_execution_without_saving_script(self, start_execution):
        content = 'print("temporary replay")'

        response = self.client.post(
            '/api/ui-automation/test-scripts/run-unsaved/',
            {
                'project': self.project.id,
                'content': content,
                'base_url': 'https://example.com',
                'headless': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 202)
        execution = TestExecution.objects.get(pk=response.data['id'])
        self.assertIsNone(execution.test_script)
        self.assertEqual(execution.run_config['base_url'], 'https://example.com')
        self.assertNotIn('content', execution.run_config)
        start_execution.assert_called_once_with(execution.id, analyze_script(content)['normalized_content'])
        self.assertEqual(TestScript.objects.count(), 0)

    def test_unsaved_replay_rejects_scripts_outside_the_safe_subset(self):
        response = self.client.post(
            '/api/ui-automation/test-scripts/run-unsaved/',
            {
                'project': self.project.id,
                'content': 'import subprocess\nsubprocess.run(["whoami"])',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TestExecution.objects.count(), 0)
