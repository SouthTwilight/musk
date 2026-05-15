from rest_framework.response import Response
from rest_framework.views import APIView
from module_layer.registry import registry


class ModuleListView(APIView):
    """返回所有已注册模块的信息，供前端动态生成菜单。"""

    def get(self, request):
        modules = []
        for info in registry.all():
            modules.append({
                "name": info.name,
                "display_name": info.display_name,
                "icon": info.icon,
                "description": info.description,
                "menu_order": info.menu_order,
                "url_prefix": info.url_prefix,
                "version": info.version,
            })
        return Response(modules)
