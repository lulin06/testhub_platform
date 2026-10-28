from rest_framework import serializers
from .models import TestPlan, TestRun, TestRunCase, TestRunCaseHistory
from apps.testcases.models import TestCase
from apps.testcases.serializers import TestCaseStepSerializer
from apps.users.serializers import UserSimpleSerializer

class TestRunCaseHistorySerializer(serializers.ModelSerializer):
    executed_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = TestRunCaseHistory
        fields = ('id', 'status', 'actual_result', 'comments', 'executed_by', 'executed_at')

class TestCaseExecutionSerializer(serializers.ModelSerializer):
    """测试计划详情中用于展示和执行弹窗的用例信息。"""
    author = UserSimpleSerializer(read_only=True)
    assignee = UserSimpleSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    step_details = TestCaseStepSerializer(many=True, read_only=True)

    class Meta:
        model = TestCase
        fields = (
            'id', 'title', 'description', 'notes', 'preconditions', 'steps',
            'expected_result', 'priority', 'test_type', 'author', 'assignee', 'project_name', 'step_details'
        )

class TestRunCaseSimpleSerializer(serializers.ModelSerializer):
    testcase = TestCaseExecutionSerializer(read_only=True)
    executed_by = UserSimpleSerializer(read_only=True)

    class Meta:
        model = TestRunCase
        fields = ('id', 'testcase', 'status', 'priority', 'actual_result', 'comments', 'executed_by', 'executed_at')

class TestRunCaseDetailSerializer(serializers.ModelSerializer):
    testcase = TestCaseExecutionSerializer(read_only=True)
    executed_by = UserSimpleSerializer(read_only=True)
    history = TestRunCaseHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = TestRunCase
        fields = ('id', 'testcase', 'status', 'priority', 'actual_result', 'comments', 
                 'defects', 'elapsed_time', 'executed_by', 'executed_at', 'created_at', 
                 'updated_at', 'history')

class TestRunSerializer(serializers.ModelSerializer):
    run_cases = TestRunCaseSimpleSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = TestRun
        fields = ('id', 'name', 'status', 'assignee', 'progress', 'run_cases')
    
    def get_progress(self, obj):
        return obj.progress_stats


class TestPlanSerializer(serializers.ModelSerializer):
    creator = UserSimpleSerializer(read_only=True)
    projects = serializers.StringRelatedField(many=True, read_only=True)
    version = serializers.StringRelatedField()

    class Meta:
        model = TestPlan
        fields = ('id', 'name', 'projects', 'version', 'creator', 'created_at', 'is_active')


class TestPlanDetailSerializer(serializers.ModelSerializer):
    test_runs = TestRunSerializer(many=True, read_only=True)
    creator = UserSimpleSerializer(read_only=True)
    projects = serializers.StringRelatedField(many=True, read_only=True)
    version = serializers.StringRelatedField()
    testcases = serializers.SerializerMethodField()

    class Meta:
        model = TestPlan
        fields = '__all__'

    def get_testcases(self, obj):
        testcase_map = {}
        for test_run in obj.test_runs.prefetch_related('testcases__project').all():
            for testcase in test_run.testcases.all():
                testcase_map[testcase.id] = {
                    'id': testcase.id,
                    'title': testcase.title,
                    'priority': testcase.priority,
                    'test_type': testcase.test_type,
                    'project__name': testcase.project.name if testcase.project else ''
                }
        return list(testcase_map.values())

class TestRunCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestRunCase
        fields = '__all__'
