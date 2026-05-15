"""数据库路由器 — 将模块查询路由到对应模块数据库。"""


class ModuleRouter:
    """根据 app_label 将查询路由到模块专属数据库。"""

    def db_for_read(self, model, **hints):
        return self._get_module_db(model)

    def db_for_write(self, model, **hints):
        return self._get_module_db(model)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # 模块 DB 只允许对应模块的迁移
        from module_layer.registry import registry

        for info in registry.all():
            if db == info.db_alias:
                return app_label == info.app_label
        # 非 module_ 前缀的 DB（如 default）不干预
        if db == "default":
            return app_label not in [info.app_label for info in registry.all()]
        return None

    def _get_module_db(self, model) -> str | None:
        from module_layer.registry import registry

        app_label = model._meta.app_label
        for info in registry.all():
            if info.app_label == app_label:
                return info.db_alias
        return None
