"""Our models are managed=False (Supabase owns the schema). For tests only, let Django
create those tables in a throw-away test database so the tests can run anywhere."""
from django.apps import apps
from django.test.runner import DiscoverRunner


class UnmanagedModelsRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        self._unmanaged = [m for m in apps.get_models() if not m._meta.managed]
        for m in self._unmanaged:
            m._meta.managed = True
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        for m in self._unmanaged:
            m._meta.managed = False
