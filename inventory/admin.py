from django import urls
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import User, Group
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _, ngettext
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

from .actions import move_to_other_location, change_category, create_sections
from .list_filters import ItemsByLocation, LocationsByLocation, ExpirationFieldListFilter, ItemsByCategory, \
    CategoriesByCategory
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

# Stock Django auth models

admin_site.register(User)
admin_site.register(Group)


class ShortTitleChangeList(ChangeList):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.title = self.opts.verbose_name_plural.capitalize()


class CustomChangeListModelAdmin(admin.ModelAdmin):
    # noinspection PyMethodMayBeStatic
    def get_changelist(self, request, **kwargs):
        return ShortTitleChangeList


# App models

def edit_icon(*a, **kw):
    edit_svg = static('admin/img/icon-changelink.svg')
    return mark_safe(
        format_lazy(f'<img style="margin-left: 50%" src="{edit_svg}" alt="{{alt}}" title="{{alt}}">', alt=_("Edit")))


edit_icon.short_description = ""


@admin.register(Item, site=admin_site)
class ItemAdmin(CustomChangeListModelAdmin):
    ordering = ('location', 'name')
    fields = (('name', 'location'), ('amount', 'unit'), 'category', 'expiration', 'description')
    search_fields = ('name',)
    list_display = (
        'link_to_name_search', 'link_to_category', 'link_to_location', 'short_amount', 'expiration', 'edit_icon')
    list_display_links = ('edit_icon',)
    list_filter = (ItemsByLocation, ItemsByCategory, 'amount', ExpirationFieldListFilter)
    actions = (move_to_other_location, change_category)
    edit_icon = edit_icon

    def link_to_name_search(self, obj: Item):
        link = urls.reverse("admin:inventory_item_changelist") + f"?q={obj.name}"
        return format_html('<a href="{}" title="{}">{}</a>', link, _("Search all %(model_name)s named \"%(name)s\"") % {
            "model_name": model_ngettext(obj, n=2),
            "name": obj.name
        }, obj.name)

    link_to_name_search.short_description = _("name")

    def link_to_location(self, obj: Item):
        if obj.location is None:
            return self.get_empty_value_display()
        link = urls.reverse("admin:inventory_location_changelist") + f"?descendants={obj.location.id}"
        return format_html('<a href="{}" title="{}">{}</a>', link, _("Explore \"%(name)s\"") % {
            "name": obj.location.name
        }, str(obj.location))

    link_to_location.short_description = _("location")

    def link_to_category(self, obj: Item):
        if obj.category is None:
            return self.get_empty_value_display()
        link = urls.reverse("admin:inventory_category_changelist") + f"?descendants={obj.category.id}"
        return format_html('<a href="{}" title="{}">{}</a>', link, _("Explore \"%(name)s\"") % {
            "name": obj.category.bcrumb_name
        }, obj.category.bcrumb_name)

    link_to_category.short_description = _("cat.")

    def short_amount(self, obj: Item):
        unit = obj.unit
        if unit == "pieces":
            unit = ngettext("piece", "pieces", obj.amount)
        return f"{obj.amount} {unit}"

    short_amount.short_description = _("qty")


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
class LocationAdmin(CustomChangeListModelAdmin, TreeNodeModelAdmin):
    treenode_display_mode = settings.LOCATIONS_DISPLAY_MODE
    form = TreeNodeForm
    list_display = ('name_link_to_items', 'edit_icon')
    list_filter = (LocationsByLocation,)
    inlines = [LocationInline, ItemInlineForLocation]
    fields = ('name', 'locator', 'tn_parent', 'description')
    actions = (create_sections,)
    list_display_links = ('edit_icon',)
    search_fields = ('name', 'locator')
    edit_icon = edit_icon

    def name_link_to_items(self, obj: Location):
        link = urls.reverse("admin:inventory_item_changelist") + f"?location={obj.id}"
        return format_html('<a href="{}" title="{}">{}</a>', link, _("See all items in \"%(name)s\"") % {
            "name": obj.name
        }, _("Items in %(name)s (%(count)d)") % {"name": obj.name, "count": obj.objects_count})

    name_link_to_items.short_description = _("items")


@admin.register(Category, site=admin_site)
class CategoryAdmin(CustomChangeListModelAdmin, TreeNodeModelAdmin):
    treenode_display_mode = settings.CATEGORIES_DISPLAY_MODE
    form = TreeNodeForm
    inlines = [ItemInlineForCategory]
    fields = ('name', 'tn_parent')
    list_display = ('name_link_to_items', 'edit_icon')
    list_display_links = ('edit_icon',)
    list_filter = (CategoriesByCategory,)
    search_fields = ('name',)
    edit_icon = edit_icon

    def name_link_to_items(self, obj: Category):
        link = urls.reverse("admin:inventory_item_changelist") + f"?category={obj.id}"
        return format_html('<a href="{}" title="{}">{}</a>', link, _("See all items in \"%(name)s\"") % {
            "name": obj.name
        }, _("Items in %(name)s (%(count)d)") % {"name": obj.name, "count": obj.objects_count})

    name_link_to_items.short_description = _("items")
