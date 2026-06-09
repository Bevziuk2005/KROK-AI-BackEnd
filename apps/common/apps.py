from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'

    def ready(self):
        # small admin UI customization and ensure admin modules are loaded
        try:
            from django.contrib import admin
            admin.site.site_header = 'KROK AI Backend Admin'
            admin.site.site_title = 'KROK AI Admin'
            admin.site.index_title = 'Administration'
        except Exception:
            pass
