import pytest
from django.test import TestCase
from module_layer.registry import registry, ModuleInfo


@pytest.mark.django_db
class TestModuleRegistry(TestCase):
    def setUp(self):
        registry.clear()

    def test_register_and_get(self):
        info = ModuleInfo(name="test", version="1.0", display_name="Test", icon="T")
        registry.register(info)
        assert registry.get("test") == info

    def test_all_sorted_by_menu_order(self):
        registry.register(ModuleInfo(name="b", version="1", display_name="B", icon="B", menu_order=2))
        registry.register(ModuleInfo(name="a", version="1", display_name="A", icon="A", menu_order=1))
        names = [m.name for m in registry.all()]
        assert names == ["a", "b"]

    def test_clear(self):
        registry.register(ModuleInfo(name="x", version="1", display_name="X", icon="X"))
        registry.clear()
        assert registry.get("x") is None
