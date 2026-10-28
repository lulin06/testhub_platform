"""
将 Katana 后端的 OpenAPI 规范导入到 TestHub 的「接口管理」(api-testing)。

用法:
    # 预览（不改动任何数据），输出将删除 / 将创建的数量
    python manage.py import_katana_openapi

    # 真正执行：先清空现有 api-testing 数据，再按规范重建
    python manage.py import_katana_openapi --confirm

可选参数:
    --spec PATH            OpenAPI JSON 文件路径
                          默认: /Users/a123456/Desktop/Pear automation/docs/api/katana-server.openapi.json
    --project-name NAME    导入后生成的项目名（默认: Katana API）
    --base-url URL         覆盖规范里的 server 地址

数据映射:
    OpenAPI tag(module)  -> ApiCollection(按模块分组, 挂在根集合下)
    OpenAPI operation    -> ApiRequest
        method      = HTTP method
        url         = <server 基础地址> + <path>   (完整绝对 URL, 含 {path} 占位)
        params      = query 参数 (dict: 名称 -> 示例/空串)
        headers     = header 参数 + JSON 体的 Content-Type
        body        = {"type":"json","data":<示例对象>}  (由 schema 递归生成)
"""
import os
import json

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from apps.api_testing.models import (
    ApiProject,
    ApiCollection,
    ApiRequest,
)

User = get_user_model()

DEFAULT_SPEC = "/Users/a123456/Desktop/Pear automation/docs/api/katana-server.openapi.json"

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class Command(BaseCommand):
    help = "将 Katana OpenAPI 规范导入接口管理（清空后重建）。不加 --confirm 为预览。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--spec",
            default=DEFAULT_SPEC,
            help="OpenAPI JSON 文件路径 (默认: %(default)s)",
        )
        parser.add_argument(
            "--project-name",
            default="Katana API",
            help="导入生成的项目名称 (默认: Katana API)",
        )
        parser.add_argument(
            "--base-url",
            default=None,
            help="覆盖规范里的 server 基础地址",
        )
        parser.add_argument(
            "--owner",
            default=None,
            help="项目 owner / 请求 created_by 的用户名（默认: 第一个超级用户）",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="真正执行删除与导入；不加则只做预览",
        )

    # ---------- schema 示例生成 ----------
    def build_sample(self, schema, components, depth=0):
        if not isinstance(schema, dict):
            return None
        if "$ref" in schema:
            ref = schema["$ref"]
            node = components
            for part in ref.lstrip("#/").split("/"):
                if not isinstance(node, dict):
                    return None
                node = node.get(part, {})
            return self.build_sample(node, components, depth)
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        typ = schema.get("type")
        if typ == "object" or "properties" in schema:
            if depth > 6:
                return {}
            result = {}
            for k, v in schema.get("properties", {}).items():
                result[k] = self.build_sample(v, components, depth + 1)
            return result
        if typ == "array":
            sample = self.build_sample(schema.get("items", {}), components, depth + 1)
            return [sample] if sample is not None else []
        if typ == "string":
            fmt = schema.get("format")
            if fmt == "date-time":
                return "2024-01-01T00:00:00Z"
            if fmt == "date":
                return "2024-01-01"
            if fmt in ("binary", "byte"):
                return ""
            return "string"
        if typ == "integer":
            return 0
        if typ == "number":
            return 0.0
        if typ == "boolean":
            return True
        if typ == "null":
            return None
        # allOf / oneOf / anyOf
        for comb in ("allOf", "oneOf", "anyOf"):
            if comb in schema and isinstance(schema[comb], list):
                merged = {}
                for sub in schema[comb]:
                    sub_sample = self.build_sample(sub, components, depth + 1)
                    if isinstance(sub_sample, dict):
                        merged.update(sub_sample)
                return merged
        return None

    # ---------- 主流程 ----------
    def handle(self, *args, **options):
        spec_path = options["spec"]
        project_name = options["project_name"]
        base_url_override = options["base_url"]
        confirm = options["confirm"]

        if not os.path.isfile(spec_path):
            raise CommandError(f"找不到 OpenAPI 文件: {spec_path}")

        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        components = spec.get("components", {})
        servers = spec.get("servers") or [{"url": "https://release.katana-api.1m.app"}]
        base_url = (base_url_override or servers[0].get("url", "")).rstrip("/")

        paths = spec.get("paths", {})

        # 模块（tag）顺序：优先用顶层 tags 定义顺序，保证与文档一致
        tag_order = [t.get("name") for t in spec.get("tags", []) if t.get("name")]
        tag_seen = set(tag_order)

        # 解析 operation -> request 草稿
        tag_collections = {}  # tag -> list of request dicts
        root_requests = []    # 没有 tag 的 operation
        op_count = 0

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op in path_item.items():
                if method.upper() not in HTTP_METHODS:
                    continue
                if not isinstance(op, dict):
                    continue
                op_count += 1

                op_tags = op.get("tags") or []
                tag = op_tags[0] if op_tags else None
                if tag and tag not in tag_seen:
                    tag_seen.add(tag)
                    tag_order.append(tag)

                summary = op.get("summary") or op.get("operationId") or f"{method.upper()} {path}"
                url = f"{base_url}{path}"

                params = {}      # query 参数
                headers = {}     # header 参数
                for p in op.get("parameters", []) or []:
                    pname = p.get("name")
                    pin = p.get("in")
                    if not pname or not pin:
                        continue
                    pSchema = p.get("schema", {}) or {}
                    example = pSchema.get("example")
                    if example is None and "default" in pSchema:
                        example = pSchema["default"]
                    if pin == "query":
                        params[pname] = "" if example is None else example
                    elif pin == "header":
                        headers[pname] = "" if example is None else example

                body = {"type": "none", "data": None}
                req_body = op.get("requestBody", {}) or {}
                content = req_body.get("content", {}) or {}
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {}) or {}
                    data = self.build_sample(schema, components)
                    body = {"type": "json", "data": data}
                    headers.setdefault("Content-Type", "application/json")
                elif "application/x-www-form-urlencoded" in content:
                    props = (content["application/x-www-form-urlencoded"]
                             .get("schema", {}).get("properties", {}))
                    body = {"type": "x-www-form-urlencoded",
                            "data": [{"key": k, "value": "", "enabled": True}
                                     for k in props]}
                elif "multipart/form-data" in content:
                    props = (content["multipart/form-data"]
                             .get("schema", {}).get("properties", {}))
                    body = {"type": "form-data",
                            "data": [{"key": k, "value": "", "enabled": True}
                                     for k in props]}

                req_draft = {
                    "name": summary,
                    "description": op.get("description", "") or "",
                    "method": method.upper(),
                    "url": url,
                    "params": params,
                    "headers": headers,
                    "body": body,
                }
                if tag:
                    tag_collections.setdefault(tag, []).append(req_draft)
                else:
                    root_requests.append(req_draft)

        # ---------- 输出预览 ----------
        self.stdout.write(self.style.MIGRATE_HEADING("OpenAPI 解析结果"))
        self.stdout.write(f"  规范文件      : {spec_path}")
        self.stdout.write(f"  基础地址      : {base_url}")
        self.stdout.write(f"  路径数        : {len(paths)}")
        self.stdout.write(f"  操作数        : {op_count}")
        self.stdout.write(f"  模块(tag)数   : {len(tag_collections) + (1 if root_requests else 0)}")
        self.stdout.write(f"  计划集合数    : {len(tag_collections) + (1 if root_requests else 0)} 个模块 + 1 个根集合")
        self.stdout.write(f"  计划请求数    : {op_count}")

        # 现有数据
        exist_projects = ApiProject.objects.count()
        exist_collections = ApiCollection.objects.count()
        exist_requests = ApiRequest.objects.count()
        self.stdout.write(self.style.MIGRATE_HEADING("当前 api-testing 数据（将被清空）"))
        self.stdout.write(f"  ApiProject    : {exist_projects}")
        self.stdout.write(f"  ApiCollection : {exist_collections}")
        self.stdout.write(f"  ApiRequest    : {exist_requests}")

        if not confirm:
            self.stdout.write(self.style.WARNING(
                "\n[预览模式] 未加 --confirm，未做任何改动。"
                "确认无误后加上 --confirm 执行清空并导入。"
            ))
            return

        # ---------- 确认执行 ----------
        owner = None
        if options.get("owner"):
            owner = User.objects.filter(username=options["owner"]).first()
            if not owner:
                raise CommandError(f"找不到用户: {options['owner']}")
        if not owner:
            owner = (
                User.objects.filter(is_superuser=True).first()
                or User.objects.filter(is_staff=True).first()
                or User.objects.first()
            )
        if not owner:
            raise CommandError("找不到任何用户作为 owner/created_by，无法导入。请先创建超级用户。")

        self.stdout.write(self.style.MIGRATE_HEADING("开始清空现有 api-testing 数据"))
        # 先删请求，再删集合，再删项目（避免外键悬挂）；级联会一并清理套件/定时任务等
        n_req = ApiRequest.objects.all().delete()[0]
        n_col = ApiCollection.objects.all().delete()[0]
        n_proj = ApiProject.objects.all().delete()[0]
        self.stdout.write(f"  已删除 ApiRequest={n_req}  ApiCollection={n_col}  ApiProject={n_proj}")

        self.stdout.write(self.style.MIGRATE_HEADING("开始导入 Katana 规范"))
        project = ApiProject.objects.create(
            name=project_name,
            description=f"由 Katana OpenAPI 规范自动导入（{base_url}）",
            project_type="HTTP",
            status="IN_PROGRESS",
            owner=owner,
        )
        project.members.add(owner)

        root_collection = ApiCollection.objects.create(
            name=f"{project_name} ({base_url})",
            description="Katana 后端接口（按模块分组）",
            project=project,
            parent=None,
            order=0,
        )

        created_requests = 0
        for order, tag in enumerate(tag_order):
            drafts = tag_collections.get(tag, [])
            if not drafts:
                continue
            tag_coll = ApiCollection.objects.create(
                name=tag,
                description=f"{tag} 模块（{len(drafts)} 个端点）",
                project=project,
                parent=root_collection,
                order=order,
            )
            ApiRequest.objects.bulk_create([
                ApiRequest(
                    collection=tag_coll,
                    name=d["name"][:200],
                    description=d["description"] or "",
                    method=d["method"],
                    url=d["url"],
                    headers=d["headers"],
                    params=d["params"],
                    body=d["body"],
                    created_by=owner,
                    order=i,
                )
                for i, d in enumerate(drafts)
            ])
            created_requests += len(drafts)
            self.stdout.write(f"  [模块] {tag:<28} 集合已建, 请求 {len(drafts)}")

        if root_requests:
            ApiRequest.objects.bulk_create([
                ApiRequest(
                    collection=root_collection,
                    name=d["name"][:200],
                    description=d["description"] or "",
                    method=d["method"],
                    url=d["url"],
                    headers=d["headers"],
                    params=d["params"],
                    body=d["body"],
                    created_by=owner,
                    order=i,
                )
                for i, d in enumerate(root_requests)
            ])
            created_requests += len(root_requests)
            self.stdout.write(f"  [未分类] 请求 {len(root_requests)}")

        self.stdout.write(self.style.SUCCESS(
            f"\n导入完成: 项目 1 个, 根集合 1 个, 模块集合 {len(tag_collections)} 个, "
            f"请求 {created_requests} 个 (owner={owner})。"
        ))
