from django.db import models
from django.template.loader import render_to_string
from unittest.util import _MAX_LENGTH
    
class RemoteWMSInstance(models.Model):
    name=models.CharField(max_length=60, default="RemoteLayer")
    wmsURL=models.CharField(max_length=300, default="http://www.geoportal.eb.mil.br/ms")
    def __str__(self):
        return self.name+": "+self.wmsURL
    
    #Read layers from remote connection using a GetCapabilities request
    def ReadLayersFromServer(self):
        #let's begin connecting.
        from owslib.wms import WebMapService
        wms = WebMapService(self.wmsURL)
        #clean the old records on table Layer connected to this RemoteWMSInstance
        oldLayers=CachedLayer.objects.filter(connection=self)
        for oldLayer in oldLayers: oldLayer.delete() 
        #read the contents from GetCapabilities and add the layers as new records
        for layer in wms.contents:
            RLayer=CachedLayer() #creating a new Layer Object
            RLayer.layername=layer
            RLayer.wmsLayerName=layer
            RLayer.title=wms[layer].title
            if (wms[layer].abstract): #not null
                RLayer.abstract=wms[layer].abstract
            RLayer.connection=self #Point the ForeignKey to this RemoteWMSInstance
            RLayer.save() #stores the new layer on the database
    
class CachedLayer(models.Model):
    abstract=models.TextField(blank=True)
    title=models.CharField(max_length=200, blank=True)
    layername= models.CharField(max_length=60, default="NewLayer")
    connection=models.ForeignKey(RemoteWMSInstance,  on_delete=models.CASCADE)
    def __str__(self):
        return "%s - %s" % (self.layername, self.connection.wmsURL)
    def isPublished(self):
        publishedOn=self.mapcacheinstance_set.all()
        if len(publishedOn)>0 :
            return publishedOn
        else:
            return 'Unpublished'
    def reseed(self):
        import os


import os
import signal
import subprocess
class MapCacheSeedProcess(models.Model):
    pid=models.IntegerField(blank=True)
    startTime=models.DateTimeField(auto_now_add=True, blank=True)
    mapcacheinstance=models.ForeignKey('MapCacheInstance', on_delete=models.CASCADE)
    
    layer=models.ForeignKey(CachedLayer, on_delete=models.CASCADE)
    parameters=models.CharField(max_length=200,blank=True)
    def save(self, *args, **kwargs):
        if not self.pid:
            #TO DO: THIS SHOULD ITERATE OVER EVERY MAPCACHE
            parameters=["mapcache_seed","-c",self.mapcacheinstance.mapCacheXmlPath,'-t',self.layer.layername,"-z","0,8"]
            print(parameters)
            self.pid = subprocess.Popen(parameters, stdout=None).pid
        super(MapCacheSeedProcess, self).save(*args, **kwargs)
    
    def is_process_running(self):
        try:
            os.kill(self.pid, 0)
            return True
        except OSError:
            return False
    
    def kill(self):
        if self.is_process_running():
            os.kill(self.pid, signal.SIGTERM)
    def delete(self, *args, **kwargs):
        self.kill()
        super(MapCacheSeedProcess, self).delete(*args, **kwargs)
    def update(self):
        
        if not self.is_process_running(): #this is not what it looks like. It's just to CHECK if it's running.
            print ("tentando remover")
            self.delete()
        
    def __str__(self):
        return "%s %s %s %s" % (self.pid, self.startTime, self.layer, self.mapcacheinstance )

class MapCacheInstance(models.Model):
    name=models.CharField(max_length=60, default="WSProvider")
    mapCacheXmlPath=models.CharField(max_length=300, default="/var/www/html/fonte/map/msmosaic.xml")
    mapCacheUrl=models.CharField(max_length=300, default="http://localhost/cgi-bin/mapcache?")
    publishedLayers=models.ManyToManyField(CachedLayer,  blank=True)
    
    def __str__(self):
        return "%s - %s" % (self.mapCacheXmlPath, self.mapCacheUrl)
    
    def save(self, *args, **kwargs):
        import os
        super(MapCacheInstance, self).save(*args, **kwargs)
        #Template file, any human that knows XML can change it
        template = 'mapcacheconf/MapCacheTemplate.xml'
        #The variable on context will be passed to the template to fill the XML
        context = { 
            'layers': self.publishedLayers.all(), 
            'mapCacheUrl': self.mapCacheUrl
        }
        #Prepare the directory for the new file
        directory=os.path.dirname(self.mapCacheXmlPath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        #save the XML on disk
        import codecs
        codecs.open(self.mapCacheXmlPath, 'w', 'utf-8').write(render_to_string(template, context))
    
