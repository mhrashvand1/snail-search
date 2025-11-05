from django.db import models


class Base(models.Model):
    created_date = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    modified_date = models.DateTimeField("تاریخ ویرایش", auto_now=True)

    class Meta:
        abstract = True