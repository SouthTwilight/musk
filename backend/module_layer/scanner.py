"""自动模块扫描器 — 遍历 apps/ 目录，发现并注册模块。"""

import importlib
import importlib.util
import logging
from pathlib import Path

from django.conf import settings

from module_layer.registry import registry, ModuleInfo

logger = logging.getLogger(__name__)

APPS_DIR = Path(settings.BASE_DIR) / "apps"


def _load_manifest(app_path: Path) -> dict | None:
    """从模块目录读取 manifest.py 中的 MANIFEST 字典。"""
    manifest_path = app_path / "manifest.py"
    if not manifest_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("manifest", manifest_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return getattr(module, "MANIFEST", None)
    except Exception as e:
        logger.warning("Failed to load manifest from %s: %s", app_path, e)
        return None


def _validate_manifest(data: dict) -> list[str]:
    """校验 manifest 必填字段，返回错误列表。"""
    errors = []
    for field in ("name", "version", "display_name", "icon"):
        if field not in data:
            errors.append(f"Missing required field: {field}")
    return errors


def scan_modules() -> list[ModuleInfo]:
    """扫描 apps/ 目录，发现并注册所有合规模块。返回已注册模块列表。"""
    discovered = []

    if not APPS_DIR.exists():
        logger.info("apps/ directory does not exist, skipping scan")
        return discovered

    for app_path in APPS_DIR.iterdir():
        if not app_path.is_dir():
            continue
        if app_path.name.startswith("_"):
            continue

        data = _load_manifest(app_path)
        if data is None:
            continue

        errors = _validate_manifest(data)
        if errors:
            logger.warning("Invalid manifest in %s: %s", app_path.name, errors)
            continue

        info = ModuleInfo(
            name=data["name"],
            version=data["version"],
            display_name=data["display_name"],
            icon=data["icon"],
            description=data.get("description", ""),
            menu_order=data.get("menu_order", 99),
            app_label=f"apps_{app_path.name}",
            db_alias=f"module_{data['name']}",
            url_prefix=f"/api/{data['name']}/",
            dependencies=data.get("dependencies", []),
            ai_templates=data.get("ai_templates", []),
        )

        registry.register(info)
        discovered.append(info)
        logger.info("Registered module: %s v%s", info.name, info.version)

    return discovered


def get_module_databases() -> dict:
    """为所有已注册模块生成 DATABASES 配置。每个模块独立 SQLite 文件。"""
    databases = {}
    db_dir = Path(settings.BASE_DIR).parent / getattr(settings, "DB_DIR", "data")

    for info in registry.all():
        db_path = db_dir / f"{info.name}.db"
        databases[info.db_alias] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(db_path),
        }

    return databases
