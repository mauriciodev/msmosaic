from django.contrib import admin

# Register your models here.

from .models import MapCacheInstance
admin.site.register(MapCacheInstance)

#RemoteWMSInstance
from .models import RemoteWMSInstance
class RemoteWMSInstanceAdmin(admin.ModelAdmin):
    def readLayersFromServer(self,request, queryset):
        for RemoteWMS in queryset:
            RemoteWMS.ReadLayersFromServer()   
    readLayersFromServer.short_description = "Read layers from selected remote WMS servers"
    actions = [readLayersFromServer]   
admin.site.register(RemoteWMSInstance, RemoteWMSInstanceAdmin)


#MapCacheSeedProcess
from .models import MapCacheSeedProcess
class MapCacheSeedProcessAdmin(admin.ModelAdmin):
    def updateProcessessState(self,request, queryset):
        for row in queryset:
            row.update()   
    updateProcessessState.short_description = "Update process status"
    actions = [updateProcessessState]   
admin.site.register(MapCacheSeedProcess, MapCacheSeedProcessAdmin)

#CachedLayer
from .models import CachedLayer
class CachedLayerAdmin(admin.ModelAdmin):
    list_display = ['layername', 'connection','isPublished']
    ordering = ['layername','connection']
    search_fields = ['layername']
    list_filter = ['connection']
admin.site.register(CachedLayer, CachedLayerAdmin)

