from django.apps import AppConfig


class HorizonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'horizon'

    def ready(self):
        """Auto-apply any pending migrations on startup so new tables exist immediately."""
        try:
            from django.db import connection
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                from django.core.management import call_command
                call_command('migrate', verbosity=0, interactive=False)
        except Exception:
            pass
