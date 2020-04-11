from django.contrib import admin

from bookstore import models


class AuthorAdmin(admin.ModelAdmin):
    pass


class BookAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Author, AuthorAdmin)
admin.site.register(models.Book, BookAdmin)
