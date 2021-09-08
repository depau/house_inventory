from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin, helpers
from django.contrib.admin.utils import model_ngettext
from django.db.models import QuerySet
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from inventory.models import Location, Category


@admin.action(description=_("Move items to another location"), permissions=['change'])
def move_to_other_location(modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet):
    # noinspection PyProtectedMember
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # The user has already confirmed the change
    if request.POST.get('post'):
        n = queryset.count()
        if n:
            loc_id = request.POST.get("new_location")
            if not loc_id:
                modeladmin.message_user(request, _("Failed to move %(items)s: no location selected") % {
                    "items": model_ngettext(modeladmin.opts, n)
                }, messages.ERROR)
                return None
            location = Location.objects.get(pk=int(loc_id))
            for obj in queryset:
                obj_display = str(obj)
                modeladmin.log_change(request, obj, obj_display)
            queryset.update(location=location)
            modeladmin.message_user(request, _("Successfully moved %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            }, messages.SUCCESS)
        return None

    if queryset.count() > 1:
        objects_name = model_ngettext(queryset)
    else:
        objects_name = str(queryset.first())

    title = _("Moving %(name)s to new location") % {"name": objects_name}

    context = {
        **modeladmin.admin_site.each_context(request),
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'title': title,
        'objects_name': str(objects_name),
        'locations': Location.objects.all(),
        'queryset': queryset,
        'model_count': queryset.count(),
        'opts': opts,
        'media': modeladmin.media,
    }

    request.current_app = modeladmin.admin_site.name

    return TemplateResponse(request, ["move_to_other_location.html"], context)


@admin.action(description=_("Change items categories"), permissions=['change'])
def change_category(modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet):
    # noinspection PyProtectedMember
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # The user has already confirmed the change
    if request.POST.get('post'):
        n = queryset.count()
        if n:
            cat_id = request.POST.get("new_category")
            if not cat_id:
                category = None
            else:
                category = Category.objects.get(pk=int(cat_id))

            for obj in queryset:
                obj_display = str(obj)
                modeladmin.log_change(request, obj, obj_display)
            queryset.update(category=category)
            modeladmin.message_user(request, _("Successfully updated %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            }, messages.SUCCESS)
        return None

    objects_name = model_ngettext(queryset)

    title = _("Changing %(name)s categories") % {"name": objects_name}

    context = {
        **modeladmin.admin_site.each_context(request),
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'title': title,
        'objects_name': str(objects_name),
        'categories': Category.objects.all(),
        'queryset': queryset,
        'model_count': queryset.count(),
        'opts': opts,
        'media': modeladmin.media,
    }

    request.current_app = modeladmin.admin_site.name

    return TemplateResponse(request, ["change_category.html"], context)


@admin.action(description=_("Create sections"), permissions=['add'])
def create_sections(modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet):
    # noinspection PyProtectedMember
    opts = modeladmin.model._meta

    n = queryset.count()
    if n != 1:
        modeladmin.message_user(request, _("Select exactly one location in order to add sections to it"), messages.ERROR)
        return None

    location = queryset.first()

    # The user has already confirmed the change
    if request.POST.get('post'):
        rows = int(request.POST.get("rows"))
        cols = int(request.POST.get("columns"))
        prefix = request.POST.get("locator_prefix")
        name_prefix = request.POST.get("name_prefix")
        zero_based = request.POST.get("zero_based", "off") == "on"

        if cols > ord('Z'):
            modeladmin.message_user(request, _("This is not Microsoft Excel, stop it."), messages.ERROR)
            return None

        count = 0
        for col_num in range(cols):
            col = chr(ord('A') + col_num) if cols > 1 else ""

            for row_num in range(rows):
                row_num += 0 if zero_based else 1
                row = str(row_num) if rows > 1 or rows == cols == 1 else ""

                newloc = f"{prefix}{row}{col}"
                newname = f"{name_prefix} {newloc}"
                newobj = Location.objects.create(tn_parent=location, name=newname, locator=newloc)
                modeladmin.log_addition(request, newobj, str(newobj))
                count += 1

        modeladmin.message_user(request, _("Successfully created %(count)d %(items)s.") % {
            "count": count, "items": model_ngettext(modeladmin.opts, n)
        }, messages.SUCCESS)
        return None

    objects_name = model_ngettext(queryset, n=2)

    title = _("Add sections to %(name)s") % {"name": str(location)}

    context = {
        **modeladmin.admin_site.each_context(request),
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'title': title,
        'objects_name': str(objects_name),
        'locator': str(location),
        'queryset': queryset,
        'opts': opts,
        'media': modeladmin.media,
    }

    request.current_app = modeladmin.admin_site.name

    return TemplateResponse(request, ["create_sections.html"], context)
