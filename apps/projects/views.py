from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError, models
from apps.users.models import User
from .models import Project, ProjectMember, ProjectEnvironment
from .serializers import ProjectSerializer, ProjectCreateSerializer, ProjectMemberSerializer, ProjectEnvironmentSerializer, ProjectCenterSerializer
from .services import sync_all_module_members, sync_legacy_projects

class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        # 默认只显示用户参与的项目或自己创建的项目
        user = self.request.user
        return Project.objects.filter(is_deleted=False).filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_all_projects(request):
    """获取所有项目列表，用于下拉选择等场景"""
    projects = Project.objects.filter(is_deleted=False).filter(
        models.Q(owner=request.user) | models.Q(members=request.user)
    ).distinct().values('id', 'name', 'description', 'status')
    return Response(list(projects))

class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(is_deleted=False).filter(
            models.Q(owner=self.request.user) | models.Q(members=self.request.user)
        ).distinct()

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_project_member(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        if project.owner != request.user:
            return Response({'error': '无权限添加成员'}, status=status.HTTP_403_FORBIDDEN)
        
        raw_user_id = request.data.get('user_id')
        if not raw_user_id:
            return Response({'error': '请选择要添加的成员'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            return Response({'error': '成员信息无效'}, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(id=user_id).exists():
            return Response({'error': '成员不存在'}, status=status.HTTP_400_BAD_REQUEST)
        if project.owner_id == user_id:
            return Response({'error': '项目负责人已在项目中'}, status=status.HTTP_400_BAD_REQUEST)
        if ProjectMember.objects.filter(project=project, user_id=user_id).exists():
            return Response({'error': '该成员已在项目中'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(project=project)
        except IntegrityError:
            return Response({'error': '该成员已在项目中'}, status=status.HTTP_400_BAD_REQUEST)
        sync_all_module_members(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except (Project.DoesNotExist, ValueError):
        return Response({'error': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_project_members(request, project_id):
    """获取项目成员列表"""
    try:
        project = Project.objects.get(id=project_id)
        
        # 检查用户是否有权限查看项目成员
        if not (project.owner == request.user or 
                ProjectMember.objects.filter(project=project, user=request.user).exists()):
            return Response({'error': '无权限查看项目成员'}, status=status.HTTP_403_FORBIDDEN)
        
        # 获取项目成员，包括项目所有者
        members = []
        
        # 添加项目所有者
        members.append({
            'id': project.owner.id,
            'member_id': None,
            'username': project.owner.username,
            'email': project.owner.email,
            'first_name': project.owner.first_name,
            'last_name': project.owner.last_name,
            'role': 'owner'
        })
        
        # 添加项目成员
        project_members = ProjectMember.objects.filter(project=project).select_related('user')
        for member in project_members:
            members.append({
                'id': member.user.id,
                'member_id': member.id,
                'username': member.user.username,
                'email': member.user.email,
                'first_name': member.user.first_name,
                'last_name': member.user.last_name,
                'role': member.role
            })
        
        return Response(members)
    except Project.DoesNotExist:
        return Response({'error': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_project_member(request, project_id, member_id):
    try:
        project = Project.objects.get(id=project_id)
        if project.owner != request.user:
            return Response({'error': '无权限删除成员'}, status=status.HTTP_403_FORBIDDEN)
        
        member = ProjectMember.objects.get(id=member_id, project=project)
        member.delete()
        sync_all_module_members(project)
        return Response({'message': '成员删除成功'})
    except (Project.DoesNotExist, ProjectMember.DoesNotExist):
        return Response({'error': '项目或成员不存在'}, status=status.HTTP_404_NOT_FOUND)

class ProjectEnvironmentListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectEnvironmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return ProjectEnvironment.objects.filter(
            project_id=project_id,
            project__in=Project.objects.filter(
                models.Q(owner=self.request.user) | models.Q(members=self.request.user)
            )
        )
    
    def perform_create(self, serializer):
        project_id = self.kwargs['project_id']
        if not Project.objects.filter(
            id=project_id
        ).filter(models.Q(owner=self.request.user) | models.Q(members=self.request.user)).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('无权限访问该项目')
        serializer.save(project_id=project_id)


class ProjectCenterListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectCenterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        sync_legacy_projects(self.request.user)
        return Project.objects.filter(is_deleted=False).filter(
            models.Q(owner=self.request.user) | models.Q(members=self.request.user)
        ).distinct().prefetch_related('projectmember_set')


class ProjectCenterDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectCenterSerializer

    def get_queryset(self):
        return Project.objects.filter(is_deleted=False).filter(
            models.Q(owner=self.request.user) | models.Q(members=self.request.user)
        ).distinct().prefetch_related('projectmember_set')

    def perform_destroy(self, instance):
        from django.utils import timezone
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])
