from django.conf import settings
from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.db import models


class CurrentSiteManager(models.Manager):
    "Use this to limit objects to those associated with the current site."

    use_in_migrations = True

    def __init__(self, field_name=None):
        super().__init__()
        self.__field_name = field_name

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_field_name())
        return errors

    def _check_field_name(self):
        field_name = self._get_field_name()
        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return [
                checks.Error(
                    f"CurrentSiteManager could not find a field named '{field_name}'.",
                    obj=self,
                    id="sites.E001",
                )
            ]

        return (
            [
                checks.Error(
                    f"CurrentSiteManager cannot use '{self.model._meta.object_name}.{field_name}' as it is not a foreign key or a many-to-many field.",
                    obj=self,
                    id="sites.E002",
                )
            ]
            if not field.many_to_many
            and not isinstance(field, (models.ForeignKey))
            else []
        )

    def _get_field_name(self):
        """Return self.__field_name or 'site' or 'sites'."""

        if not self.__field_name:
            try:
                self.model._meta.get_field("site")
            except FieldDoesNotExist:
                self.__field_name = "sites"
            else:
                self.__field_name = "site"
        return self.__field_name

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(**{self._get_field_name() + "__id": settings.SITE_ID})
        )
