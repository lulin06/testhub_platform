"""
旧 UI 数据工厂解析兼容入口（保留 core 的宽松行为）
新 UI 用例变量由 variable_context.UiVariableContext 独立处理
"""
from apps.core.variable_resolver import VariableResolver, resolve_variables

__all__ = ['VariableResolver', 'resolve_variables']
