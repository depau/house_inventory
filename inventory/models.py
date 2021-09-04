import treenode.models
from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(treenode.models.TreeNodeModel):
    treenode_display_field = 'name'

    name = models.CharField(_("name"), max_length=200)
    locator = models.CharField(_("locator"), max_length=50)
    description = models.TextField(_("description"), blank=True)

    def __str__(self):
        if self.parent is not None:
            return f"{str(self.parent)}.{self.locator}"
        return self.locator

    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")


class Category(treenode.models.TreeNodeModel):
    treenode_display_field = 'name'

    name = models.CharField(_("name"), max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")


class Item(models.Model):
    class Unit(models.TextChoices):
        PIECES = "pieces", "pieces"
        M = "m", "m"
        CM = "cm", "cm"
        MM = "mm", "mm"
        ML = "mL", "mL"
        L = "L", "L"

    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    amount = models.IntegerField(_("amount"), default=1)
    unit = models.CharField(_("unit"), default="pieces", choices=Unit.choices, max_length=10)
    location = models.ForeignKey(Location, null=True, on_delete=models.SET_NULL, verbose_name=_("location"))
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("category"))
    expiration = models.DateField(_("expiration"), null=True, blank=True, default=None)

    def __str__(self):
        result = self.name
        if self.unit == "pieces" and self.amount != 1:
            result += f" (x{self.amount})"
        elif self.unit != "pieces":
            return f"({self.amount} {self.unit})"
        if self.category is not None:
            result = f"{self.category.name}: {result}"
        return result

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")
