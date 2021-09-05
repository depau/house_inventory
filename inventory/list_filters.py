import datetime

from django.contrib import admin
from django.contrib.admin import ListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.utils import prepare_lookup_value
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from inventory.models import Location, Category


class ItemsByLocation(admin.SimpleListFilter):
    title = _("location")
    parameter_name = "location"

    def lookups(self, request, model_admin):
        return sorted(
            ((i.location.id, str(i.location)) for i in model_admin.model.objects.all() if i.location),
            key=lambda i: i[1]
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        location = Location.objects.get(pk=self.value())
        result = queryset.filter(location=location)
        for i in location.descendants:
            result |= queryset.filter(location=i)
        return result


class ItemsByCategory(admin.SimpleListFilter):
    title = _("category")
    parameter_name = "category"

    def lookups(self, request, model_admin):
        result = set()

        def add_item(cat: Category):
            result.add((cat.id, "/".join(map(lambda c: c.name, cat.breadcrumbs))))

        for i in model_admin.model.objects.all():
            if not i.category:
                continue
            add_item(i.category)
            list(map(add_item, i.category.ancestors))

        return sorted(result, key=lambda c: c[1])

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        category = Category.objects.get(pk=self.value())
        result = queryset.filter(category=category)
        for i in category.descendants:
            result |= queryset.filter(category=i)
        return result


class LocationsByLocation(admin.SimpleListFilter):
    title = _("container")
    parameter_name = "descendants"

    def lookups(self, request, model_admin):
        return sorted(
            ((i.id, str(i)) for i in model_admin.model.objects.all()),
            key=lambda i: i[1]
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        location = Location.objects.get(pk=self.value())
        result = queryset.filter(pk=location.id)
        for i in location.descendants:
            result |= queryset.filter(pk=i.id)
        return result


class ExpirationFieldListFilter(ListFilter):
    title = "expiration"

    def __init__(self, request, params, model, model_admin):
        field = "expiration"
        field_path = field

        self.field_generic = '%s__' % field_path
        self.date_params = {k: v for k, v in params.items() if k.startswith(self.field_generic)}

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()
        next_month = today + datetime.timedelta(days=30)

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any'), {}),
            (_('Expired'), {
                self.lookup_kwarg_until: str(today),
            }),
            (_('Expires this month'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(next_month),
            }),
            (_('Expires later'), {
                self.lookup_kwarg_since: str(next_month),
            }),
        )
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        self.links += (
            (_('Does not expire'), {self.field_generic + 'isnull': 'True'}),
            (_('Expires'), {self.field_generic + 'isnull': 'False'}),
        )

        super().__init__(field, request, params, model)

        for p in self.expected_parameters():
            if p in params:
                value = params.pop(p)
                self.used_parameters[p] = prepare_lookup_value(p, value)

    def has_output(self):
        return True

    def queryset(self, request, queryset):
        try:
            return queryset.filter(**self.used_parameters)
        except (ValueError, ValidationError) as e:
            # Fields may raise a ValueError or ValidationError when converting
            # the parameters to the correct type.
            raise IncorrectLookupParameters(e)

    def expected_parameters(self):
        params = [self.lookup_kwarg_since, self.lookup_kwarg_until, self.lookup_kwarg_isnull]
        return params

    def choices(self, changelist):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': changelist.get_query_string(param_dict, [self.field_generic]),
                'display': title,
            }
