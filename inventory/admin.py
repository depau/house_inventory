from django import urls
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, ngettext
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

from .actions import move_to_other_location, change_category, create_shelves
from .list_filters import ItemsByContainer, LocationsByContainer, ExpirationFieldListFilter
from .models import Location, Item, Category


# Custom admin site definition

class InventoryAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context.update({
            'title': _("Inventory management")
        })
        return super().index(request, extra_context)

    site_title = settings.SITE_TITLE or _("House inventory")
    site_header = settings.SITE_HEADER or _("House inventory")
    site_url = None


admin_site = InventoryAdminSite(name='admin')
# admin_site.add_action(change_category)
# admin_site.add_action(create_shelves)
# admin_site.add_action(move_to_other_location)

# Stock Django auth models

admin_site.register(User)
admin_site.register(Group)


# App models

@admin.register(Item, site=admin_site)
class ItemAdmin(admin.ModelAdmin):
    ordering = ('location', 'name')
    fields = (('name', 'location'), ('amount', 'unit'), 'expiration', 'description')
    search_fields = ('name', 'location', 'category')
    list_display = ('link_to_category', 'name', 'link_to_location', 'short_amount', 'expiration')
    list_display_links = ('name',)
    list_filter = (ItemsByContainer, 'category', 'amount', ExpirationFieldListFilter)
    actions = (move_to_other_location, change_category)

    def link_to_location(self, obj: Item):
        if obj.location is None:
            return self.get_empty_value_display()
        link = urls.reverse("admin:inventory_location_changelist") + f"?descendants={obj.location.id}"
        return format_html('<a href="{}">{}</a>', link, str(obj.location))

    link_to_location.short_description = _("location")

    def link_to_category(self, obj: Item):
        if obj.category is None:
            return self.get_empty_value_display()
        link = urls.reverse("admin:inventory_category_changelist") + f"?descendants={obj.category.id}"
        return format_html('<a href="{}">{}</a>', link, str(obj.category))

    link_to_category.short_description = _("category")

    def short_amount(self, obj: Item):
        unit = obj.unit
        if unit == "pieces":
            unit = ngettext("piece", "pieces", obj.amount)
        return f"{obj.amount} {unit}"

    short_amount.short_description = _("Amount")


class ItemInlineForLocation(admin.TabularInline):
    model = Item
    extra = 0
    fields = ('name', 'amount', 'unit', 'category', 'expiration')


class ItemInlineForCategory(admin.TabularInline):
    model = Item
    extra = 0
    fields = ('name', 'amount', 'unit', 'location', 'expiration')


class LocationInline(admin.TabularInline):
    model = Location
    extra = 0
    fields = ('name', 'locator')


@admin.register(Location, site=admin_site)
class LocationAdmin(TreeNodeModelAdmin):
    treenode_display_mode = settings.LOCATIONS_DISPLAY_MODE
    form = TreeNodeForm
    list_display = ('name', 'locator_field')
    list_filter = (LocationsByContainer,)
    inlines = [LocationInline, ItemInlineForLocation]
    fields = ('name', 'locator', 'tn_parent', 'description')
    actions = (create_shelves,)

    def locator_field(self, obj: Location):
        return str(obj)

    locator_field.short_description = _("Locator")


@admin.register(Category, site=admin_site)
class CategoryAdmin(TreeNodeModelAdmin):
    treenode_display_mode = settings.CATEGORIES_DISPLAY_MODE
    form = TreeNodeForm
    inlines = [ItemInlineForCategory]
    fields = ('name', 'tn_parent')
