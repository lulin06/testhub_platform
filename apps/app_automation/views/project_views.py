# -*- coding: utf-8 -*-
"""APP自动化项目管理视图"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
import logging

from .test_case_views import AppPagination
from ..models import AppProject
from ..serializers import (
    AppProjectSerializer,
    AppProjectCreateSerializer,
    AppProjectUpdateSerializer,
)
from apps.projects.services import ensure_workspace_project_for_module, soft_delete_module_project, sync_project_members_from_module, sync_workspace_project_from_module

logger = logging.getLogger(__name__)


class AppProjectViewSet(viewsets.ModelViewSet):
    """APP自动化项目 ViewSet"""
    queryset = AppProject.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = AppPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return AppProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppProjectUpdateSerializer
        return AppProjectSerializer

    def get_queryset(self):
        user = self.request.user
        return AppProject.objects.filter(is_deleted=False).filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        ensure_workspace_project_for_module(instance, 'app', self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        sync_project_members_from_module(instance)
        sync_workspace_project_from_module(instance, 'app')

    def perform_destroy(self, instance):
        soft_delete_module_project(instance, self.request.user)
