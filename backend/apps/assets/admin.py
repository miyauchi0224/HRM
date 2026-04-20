from django.contrib import admin
from .models import Asset, AssetCategory, AssetHistory
admin.site.register(AssetCategory)
admin.site.register(Asset)
admin.site.register(AssetHistory)
