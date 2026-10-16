from rest_framework import serializers
from .models import Project, ProjectMember, ProjectEnvironment
from .services import MODULE_LABELS, _module_model, create_unified_project, update_unified_project
from apps.users.serializers import UserSerializer

class ProjectSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name')

class ProjectEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectEnvironment
        fields = '__all__'

class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'user_id', 'role', 'joined_at']

class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(source='projectmember_set', many=True, read_only=True)
    environments = ProjectEnvironmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'owner', 'members', 'modules',
                 'environments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'modules']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        validated_data.setdefault('modules', ['ai_generation'])
        return super().create(validated_data)


class ProjectCenterSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(source='projectmember_set', many=True, read_only=True)
    member_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    modules = serializers.ListField(child=serializers.CharField(), required=False)
    module_configs = serializers.DictField(write_only=True, required=False)
    module_labels = serializers.SerializerMethodField(read_only=True)
    module_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'owner', 'members', 'member_ids',
            'modules', 'module_labels', 'module_status', 'module_configs',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'is_deleted']

    def get_module_labels(self, obj):
        return [MODULE_LABELS.get(module, module) for module in (obj.modules or [])]

    def get_module_status(self, obj):
        result = {}
        for module in ('api', 'ui', 'app', 'perf'):
            module_project = _module_model(module).all_objects.filter(workspace_project=obj).first()
            result[module] = {
                'enabled': bool(module_project and not module_project.is_deleted),
                'project_id': module_project.id if module_project else None,
            }
        for module in ('ai_generation', 'ai_testing'):
            result[module] = {'enabled': module in (obj.modules or []), 'project_id': obj.id}
        return result

    def create(self, validated_data):
        request = self.context['request']
        return create_unified_project(
            user=request.user,
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            status=validated_data.get('status', 'active'),
            modules=validated_data.get('modules', []),
            member_ids=validated_data.pop('member_ids', []),
            module_configs=validated_data.pop('module_configs', {}),
        )

    def update(self, instance, validated_data):
        request = self.context['request']
        return update_unified_project(
            instance,
            user=request.user,
            name=validated_data.get('name'),
            description=validated_data.get('description'),
            status=validated_data.get('status'),
            modules=validated_data.get('modules') if 'modules' in validated_data else None,
            member_ids=validated_data.pop('member_ids', None),
            module_configs=validated_data.pop('module_configs', {}),
        )
