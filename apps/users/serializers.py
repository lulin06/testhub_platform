from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'avatar')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'avatar', 'phone', 'department', 'position', 'is_active',
                 'date_joined', 'created_at', 'updated_at']
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm',
                 'first_name', 'last_name', 'phone', 'department', 'position']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码不一致")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    # 使用自定义校验文案，避免 DRF 的默认英文字段错误落到“登录失败”兜底提示。
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=False)
    
    def validate(self, attrs):
        username = (attrs.get('username') or '').strip()
        password = attrs.get('password') or ''

        if not username and not password:
            raise serializers.ValidationError('请输入用户名和密码', code='credentials_required')
        if not username:
            raise serializers.ValidationError('请输入用户名', code='username_required')
        if not password:
            raise serializers.ValidationError('请输入密码', code='password_required')

        # 先查用户再校验密码，这样停用用户可以得到明确提示；密码不匹配仍使用
        # 统一文案，避免暴露普通账号是否存在。
        user = User.objects.filter(username=username).first()
        if user and not user.is_active:
            raise serializers.ValidationError('用户已被禁用', code='account_disabled')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('用户名或密码错误', code='invalid_credentials')
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=6, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '两次输入的新密码不一致'})
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
