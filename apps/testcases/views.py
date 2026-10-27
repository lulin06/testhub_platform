from django.http import FileResponse
from rest_framework import generics, permissions, status, pagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import models
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework import serializers

from .models import TestCase, TestCaseStep, TestCaseAttachment, TestCaseComment, TestCaseImportRecord
from .serializers import (
    TestCaseSerializer, TestCaseListSerializer, TestCaseCreateSerializer, TestCaseUpdateSerializer,
    TestCaseImportRecordListSerializer, TestCaseImportRecordDetailSerializer
)
from apps.projects.models import Project
from apps.users.models import User
from .services import TestCaseImportTemplateService, TestCaseExcelImportService
from .tasks import import_testcases_from_excel

class TestCasePagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TestCaseImportRecordPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def get_user_accessible_projects(user):
    return Project.objects.filter(
        models.Q(owner=user) | models.Q(members=user)
    ).distinct()

class TestCaseListCreateView(generics.ListCreateAPIView):
    queryset = TestCase.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TestCasePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['priority', 'test_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TestCaseCreateSerializer
        return TestCaseListSerializer

    def get_queryset(self):
        user = self.request.user
        accessible_projects = get_user_accessible_projects(user)
        queryset = TestCase.objects.filter(
            project__in=accessible_projects
        ).select_related(
            'author', 'assignee', 'project'
        ).prefetch_related(
            'versions'
        ).distinct()
        # 支持多项目过滤：project=1,2,3（单值 project=1 同样兼容）
        project_param = self.request.query_params.get('project')
        if project_param:
            project_ids = [int(pid) for pid in project_param.split(',') if pid.strip().isdigit()]
            if project_ids:
                queryset = queryset.filter(project_id__in=project_ids)
        maintainer_param = self.request.query_params.get('maintainer')
        if maintainer_param and maintainer_param.isdigit():
            queryset = queryset.filter(author_id=int(maintainer_param))
        return queryset
    
    def get_user_accessible_projects(self, user):
        """获取用户有权限访问的项目"""
        return get_user_accessible_projects(user)
    
    def perform_create(self, serializer):
        user = self.request.user
        project_id = self.request.data.get('project_id')
        
        # 获取用户有权限的项目
        accessible_projects = self.get_user_accessible_projects(user)
        
        if project_id:
            # 检查指定的项目是否存在且用户有权限
            try:
                project = accessible_projects.get(id=project_id)
            except Project.DoesNotExist:
                # 如果指定项目不存在或无权限，使用第一个可访问的项目
                project = accessible_projects.first()
                if not project:
                    # 如果用户没有任何项目，创建默认项目
                    project = Project.objects.create(
                        name="默认项目",
                        owner=user,
                        description='系统自动创建的默认项目'
                    )
        else:
            # 没有指定项目，使用第一个可访问的项目
            project = accessible_projects.first()
            if not project:
                # 如果用户没有任何项目，创建默认项目
                project = Project.objects.create(
                    name="默认项目",
                    owner=user,
                    description='系统自动创建的默认项目'
                )
        
        maintainer_id = serializer.validated_data.pop('maintainer_id', None)
        maintainer = user
        if maintainer_id:
            from apps.projects.models import ProjectMember
            if maintainer_id != project.owner_id and not ProjectMember.objects.filter(project=project, user_id=maintainer_id).exists():
                raise serializers.ValidationError({'maintainer_id': '维护人必须是项目成员'})
            maintainer = User.objects.filter(id=maintainer_id).first()
            if not maintainer:
                raise serializers.ValidationError({'maintainer_id': '维护人不存在'})
        serializer.save(author=maintainer, project=project)

class TestCaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TestCase.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TestCaseUpdateSerializer
        return TestCaseSerializer
    
    def get_queryset(self):
        user = self.request.user
        accessible_projects = get_user_accessible_projects(user)
        return TestCase.objects.filter(
            project__in=accessible_projects
        ).select_related(
            'author', 'assignee', 'project'
        ).prefetch_related(
            'versions', 'step_details', 'attachments', 'comments'
        )
    
    def get_user_accessible_projects(self, user):
        """获取用户有权限访问的项目"""
        return get_user_accessible_projects(user)
    
    def perform_update(self, serializer):
        user = self.request.user
        project_id = self.request.data.get('project_id')
        
        maintainer_id = serializer.validated_data.pop('maintainer_id', None)
        project = None
        if project_id:
            # 检查指定的项目是否存在且用户有权限
            accessible_projects = self.get_user_accessible_projects(user)
            try:
                project = accessible_projects.get(id=project_id)
            except Project.DoesNotExist:
                raise serializers.ValidationError({'project_id': '项目不存在或无权访问'})
        project = project or serializer.instance.project
        save_kwargs = {}
        if project_id and project is not None:
            save_kwargs['project'] = project
        if maintainer_id is not None:
            from apps.projects.models import ProjectMember
            if maintainer_id != project.owner_id and not ProjectMember.objects.filter(project=project, user_id=maintainer_id).exists():
                raise serializers.ValidationError({'maintainer_id': '维护人必须是项目成员'})
            maintainer = User.objects.filter(id=maintainer_id).first()
            if not maintainer:
                raise serializers.ValidationError({'maintainer_id': '维护人不存在'})
            save_kwargs['author'] = maintainer
        serializer.save(**save_kwargs)


class TestCaseNotesImageUploadView(APIView):
    """上传备注图片，备注正文只保存附件 URL，避免把图片 Base64 放进更新请求。"""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        testcase = TestCase.objects.filter(
            pk=pk,
            project__in=get_user_accessible_projects(request.user),
        ).first()
        if not testcase:
            return Response({'detail': '用例不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)

        upload = request.FILES.get('file')
        if not upload or upload.content_type not in {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}:
            return Response({'detail': '只支持 PNG、JPEG、GIF 和 WebP 图片'}, status=status.HTTP_400_BAD_REQUEST)
        if upload.size > 10 * 1024 * 1024:
            return Response({'detail': '图片大小不能超过 10MB'}, status=status.HTTP_400_BAD_REQUEST)

        attachment = TestCaseAttachment.objects.create(
            testcase=testcase,
            name=upload.name,
            file=upload,
            uploaded_by=request.user,
        )
        return Response({'url': attachment.file.url}, status=status.HTTP_201_CREATED)


class TestCaseImportTemplateDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        template_stream = TestCaseImportTemplateService.build_template()
        return FileResponse(
            template_stream,
            as_attachment=True,
            filename='testcase_import_template_v1.xlsx',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


class TestCaseImportRecordListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TestCaseImportRecordPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        return TestCaseImportRecordListSerializer

    def get_queryset(self):
        return TestCaseImportRecord.objects.filter(
            project__in=get_user_accessible_projects(self.request.user)
        ).select_related('project', 'created_by')

    def create(self, request, *args, **kwargs):
        project_id = request.data.get('project_id')
        import_file = request.FILES.get('file')

        if not project_id:
            return Response({'error': '请选择导入项目'}, status=status.HTTP_400_BAD_REQUEST)
        if not import_file:
            return Response({'error': '请上传 Excel 文件'}, status=status.HTTP_400_BAD_REQUEST)
        if not import_file.name.lower().endswith('.xlsx'):
            return Response({'error': '仅支持 .xlsx 格式文件'}, status=status.HTTP_400_BAD_REQUEST)

        accessible_projects = get_user_accessible_projects(request.user)
        try:
            project = accessible_projects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': '项目不存在或无权限访问'}, status=status.HTTP_403_FORBIDDEN)

        record = TestCaseImportRecord.objects.create(
            import_no=TestCaseExcelImportService.generate_import_no(),
            project=project,
            import_file=import_file,
            created_by=request.user,
            template_version='v1'
        )

        from apps.core.task_queue import enqueue_task
        task_id = enqueue_task(import_testcases_from_excel, record.id)
        record.celery_task_id = task_id
        record.save(update_fields=['celery_task_id', 'updated_at'])

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TestCaseImportRecordDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TestCaseImportRecordDetailSerializer
    queryset = TestCaseImportRecord.objects.select_related('project', 'created_by')

    def get_queryset(self):
        return super().get_queryset().filter(
            project__in=get_user_accessible_projects(self.request.user)
        )


class TestCaseImportFailureReportDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        record = TestCaseImportRecord.objects.filter(
            pk=pk,
            project__in=get_user_accessible_projects(request.user)
        ).first()

        if not record:
            return Response({'error': '导入记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not record.failure_report_file:
            return Response({'error': '当前记录没有失败明细文件'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            record.failure_report_file.open('rb'),
            as_attachment=True,
            filename=record.failure_report_file.name.split('/')[-1],
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
