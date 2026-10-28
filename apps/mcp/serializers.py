from rest_framework import serializers

from .models import McpCallLog, McpPendingConfirm


class McpCallLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = McpCallLog
        fields = ['id', 'username', 'tool_name', 'args_digest', 'args_brief',
                  'client_name', 'status', 'duration_ms', 'error', 'created_at']


class McpPendingConfirmSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')
    arguments = serializers.SerializerMethodField()

    def get_arguments(self, obj):
        """Hide source text in approval-console payloads while exposing a review summary."""
        arguments = dict(obj.arguments or {})
        if obj.tool_name == 'confirm_import_recorded_script' and 'content' in arguments:
            content = arguments.pop('content')
            arguments['content_summary'] = {
                'bytes': len(content.encode('utf-8')) if isinstance(content, str) else 0,
                'sha256': arguments.get('content_hash', ''),
            }
        if obj.tool_name == 'confirm_import_recorded_script' and 'start_url' in arguments:
            arguments.pop('start_url')
            arguments['has_start_url'] = True
        return arguments

    class Meta:
        model = McpPendingConfirm
        fields = ['id', 'username', 'tool_name', 'preview', 'arguments',
                  'status', 'awaiting_human', 'result', 'expires_at',
                  'created_at', 'updated_at']
