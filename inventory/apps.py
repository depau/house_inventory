from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
from django.utils.translation import ugettext_lazy as _


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = _("inventory")


class InventoryAdminConfig(AdminConfig):
    default_site = 'inventory.admin.InventoryAdminSite'
