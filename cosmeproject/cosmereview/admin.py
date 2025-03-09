from django.contrib import admin

# Register your models here.

# 管理画面で操作が可能に
from .models import Cosme, Review, Brand, Category, Tag, Email, SearchHistory
admin.site.register(Cosme)
admin.site.register(Review)
admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Email)
admin.site.register(SearchHistory)
