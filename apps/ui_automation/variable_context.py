"""UI 项目变量的运行副本；解析与存取由 UI 自动化模块独立维护。"""
from copy import deepcopy
import json
import re

from apps.core.variable_resolver import VariableResolver, resolve_variables


class VariableError(ValueError):
    """An invalid definition or unresolved runtime input."""


NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
PATH = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)(.*)\Z')
TOKEN = re.compile(r'\{\{\s*(.*?)\s*\}\}|\$\{([^{}]*)\}')
PART = re.compile(r'\.([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]')
SECRET = re.compile(r'password|passwd|secret|token|credential|api[_-]?key|cookie|authorization', re.I)
TYPES = {'string': str, 'number': (int, float), 'boolean': bool, 'array': list, 'object': dict}


def parse_path(path):
    """解析变量名、对象字段和数组下标，拒绝旧作用域路径。"""
    match = PATH.fullmatch(path.strip())
    if not match:
        raise VariableError(f'非法变量路径: {path}')
    name, rest = match.groups()
    if name in {'local', 'global'} and rest.startswith('.'):
        raise VariableError('变量引用不再支持 local/global 作用域前缀')
    parts = [name]
    while rest:
        part = PART.match(rest)
        if not part:
            raise VariableError(f'非法变量路径: {path}')
        parts.append(part[1] if part[1] is not None else int(part[2]))
        rest = rest[part.end():]
    return parts


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def _tokens(text):
    matches = list(TOKEN.finditer(text))
    remainder = TOKEN.sub('', text)
    if '{{' in remainder or '${' in remainder:
        raise VariableError('变量占位符格式无效')
    return matches


def _check_type(value, type_name):
    # null is a defined value, distinct from a missing path.
    if value is None:
        return
    if not isinstance(value, TYPES[type_name]) or (type_name == 'number' and isinstance(value, bool)):
        raise VariableError(f'变量值与声明类型 {type_name} 不匹配')
    try:
        json.dumps(value, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise VariableError('变量必须为有限的 JSON 值') from exc


class _StrictFactory(VariableResolver):
    def _evaluate_expression(self, expression):
        match = re.fullmatch(r'([A-Za-z_]\w*)\s*\((.*)\)', expression.strip(), re.S)
        name, arguments = match.groups()
        args = self._parse_args(arguments)
        if name in {'timestamp', 'timestamp_sec', 'datetime', 'date', 'time', 'date_offset'}:
            return self.functions[name](*args)
        return self.functions[name](name, args)

    def _extract_result(self, result):
        if isinstance(result, dict) and (result.get('error') or result.get('success') is False):
            # 工具错误只抛通用信息，避免把参数或凭据写入执行日志。
            raise VariableError('数据工厂工具返回错误')
        return super()._extract_result(result)


def _check_function(expression, factory):
    match = re.fullmatch(r'([A-Za-z_]\w*)\s*\((.*)\)', expression.strip(), re.S)
    if not match or match[1] not in factory.functions:
        raise VariableError('未知或非法的数据工厂函数')


def validate_variables(definitions):
    """校验定义结构和引用顺序，不执行随机函数，也不要求套件运行时数据。"""
    if not isinstance(definitions, list):
        raise VariableError('variables 必须是变量列表')
    seen = set()
    factory = _StrictFactory()
    for index, item in enumerate(definitions, 1):
        try:
            if not isinstance(item, dict):
                raise VariableError('变量定义必须为对象')
            name, kind = item.get('name'), item.get('type')
            if not isinstance(name, str) or not NAME.fullmatch(name):
                raise VariableError('名称只能使用字母、数字和下划线，且不能以数字开头')
            if 'scope' in item:
                raise VariableError('项目变量不再支持 scope 字段')
            if not isinstance(kind, str) or kind not in TYPES:
                raise VariableError('type 必须为 string/number/boolean/array/object')
            if name in seen:
                raise VariableError(f'重复变量: {name}')
            if 'value' not in item or not isinstance(item.get('description', ''), str):
                raise VariableError('必须提供 value，description 必须为文本')
            has_expression = False
            for text in _strings(item['value']):
                for token in _tokens(text):
                    has_expression = True
                    if token[1] is not None:
                        parts = parse_path(token[1])
                        if parts[0] not in seen:
                            raise VariableError(f'变量前向或循环引用: {token[1]}')
                    else:
                        _check_function(token[2], factory)
            if not has_expression:
                _check_type(item['value'], kind)
            seen.add(name)
        except VariableError as exc:
            raise VariableError(f'变量 {index}: {exc}') from exc
    return definitions


def as_text(value):
    """只在浏览器文本边界转换类型；变量上下文内部仍保留 JSON 类型。"""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


class UiVariableContext:
    def __init__(self, definitions=None, run=None, types=None):
        # 传入的 run 只作为本次套件运行的共享副本，步骤覆盖不会回写项目字段。
        self.values = run if run is not None else {}
        self.types = types if types is not None else {}
        self.temporary_names = set()
        self.factory = _StrictFactory()
        self.strict = bool(definitions)
        definitions = validate_variables([] if definitions is None else definitions)
        # 在临时副本中求值，避免定义错误时污染套件运行上下文。
        original_values = self.values
        original_types = self.types
        self.values = deepcopy(original_values)
        self.types = deepcopy(original_types)
        for item in definitions or []:
            value = self.render(item['value'])
            _check_type(value, item['type'])
            self.types[item['name']] = item['type']
            self.set(item['name'], value)
        original_values.update(self.values)
        original_types.update(self.types)
        self.values = original_values
        self.types = original_types
        self.base_values = deepcopy(self.values)

    def get(self, path):
        parts = parse_path(path)
        value = self.values
        for part in parts:
            if isinstance(part, int):
                if not isinstance(value, list) or part >= len(value):
                    raise VariableError(f'变量不存在: {path}')
            elif not isinstance(value, dict) or part not in value:
                raise VariableError(f'变量不存在: {path}')
            value = value[part]
        return deepcopy(value)

    def set(self, path, value):
        parts = parse_path(path)
        if len(parts) != 1:
            raise VariableError('设置变量只支持顶层变量名')
        name = parts[0]
        expected_type = self.types.get(name)
        if expected_type and isinstance(value, str) and expected_type != 'string':
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise VariableError(f'临时变量 {name} 必须提供有效的 JSON {expected_type} 值') from exc
        if expected_type:
            _check_type(value, expected_type)
        self.values[name] = deepcopy(value)

    def set_temporary(self, name, value):
        """将步骤结果写入当前运行副本，并登记为用例结束时清理的变量。"""
        name = str(name or '').strip()
        if not NAME.fullmatch(name):
            raise VariableError('临时变量名称只能使用字母、数字和下划线，且不能以数字开头')
        self.strict = True
        self.set(name, value)
        self.temporary_names.add(name)

    def clear(self):
        """清空当前执行副本，避免运行变量随引擎实例继续保留。"""
        self.values.clear()
        self.types.clear()
        self.base_values.clear()
        self.temporary_names.clear()

    def clear_temporary(self):
        """恢复项目变量基线，并移除当前用例设置的临时变量。"""
        for name in self.temporary_names:
            if name in self.base_values:
                self.values[name] = deepcopy(self.base_values[name])
            else:
                self.values.pop(name, None)
        self.temporary_names.clear()

    def render(self, value):
        if isinstance(value, list):
            return [self.render(item) for item in value]
        if isinstance(value, dict):
            return {key: self.render(item) for key, item in value.items()}
        if not isinstance(value, str):
            return deepcopy(value)
        matches = _tokens(value)

        def evaluate(token):
            if token[1] is not None:
                return self.get(token[1])
            _check_function(token[2], self.factory)
            try:
                return self.factory._evaluate_expression(token[2])
            except Exception as exc:
                raise VariableError('数据工厂函数执行失败') from exc

        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            return deepcopy(evaluate(matches[0]))
        # 仅替换一轮，变量值中的占位符文本不会被再次当作表达式执行。
        return TOKEN.sub(lambda token: as_text(evaluate(token)), value)

    def render_step(self, data):
        """只解析当前步骤参数；无新变量语法的旧步骤继续走原数据工厂解析器。"""
        parameters = {key: data[key] for key in ('input_value', 'assert_value') if key in data}
        if data.get('element'):
            parameters['element'] = {key: data['element'][key] for key in ('locator_value', 'locator_options') if key in data['element']}
        # 用例声明变量或步骤使用 {{...}} 后，该步骤进入严格解析模式。
        strict = self.strict or any('{{' in text for text in _strings(parameters))
        self.strict = strict
        def legacy(value):
            if isinstance(value, dict):
                return {key: legacy(item) for key, item in value.items()}
            if isinstance(value, list):
                return [legacy(item) for item in value]
            return resolve_variables(value)
        rendered = self.render(parameters) if strict else legacy(parameters)
        result = {**data, **rendered}
        if 'element' in rendered:
            result['element'] = {**data['element'], **rendered['element']}
        return result

    def apply_step(self, data):
        """处理仅作用于当前运行副本的临时变量步骤。"""
        action = data.get('action_type')
        if action == 'setVariable':
            name = str(data.get('input_value') or '').strip()
            self.set_temporary(name, data.get('assert_value'))
            return True, f'临时变量 {name} 已设置', None
        return None

    def snapshot(self):
        def mask(value):
            if isinstance(value, dict):
                return {key: '***' if SECRET.search(str(key)) else mask(item) for key, item in value.items()}
            if isinstance(value, list):
                return [mask(item) for item in value]
            return deepcopy(value)
        snapshot = mask(self.values)
        # 凭据可能被复制到普通变量名下；快照中的字符串别名也要脱敏。
        def aliases(value):
            if isinstance(value, dict):
                return {key: aliases(item) for key, item in value.items()}
            if isinstance(value, list):
                return [aliases(item) for item in value]
            return self.redact(value) if isinstance(value, str) else value
        return aliases(snapshot)

    def redact(self, text):
        def secrets(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if SECRET.search(str(key)):
                        yield from _strings(item)
                    else:
                        yield from secrets(item)
            elif isinstance(value, list):
                for item in value:
                    yield from secrets(item)
        # 按长度从长到短替换，防止短凭据先替换后破坏长凭据匹配。
        for secret in sorted(set(secrets(self.values)), key=len, reverse=True):
            if secret:
                text = text.replace(secret, '***')
        return text
