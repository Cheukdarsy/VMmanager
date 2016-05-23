from django.db import models

# Create your models here.

from django.db import models

# Create your models here.
class App(models.Model):
    full_name = models.CharField(max_length=40, default= "unknow")
    name = models.CharField(max_length=10)
    ip = models.GenericIPAddressField(protocol='ipv4',default = "0.0.0.0")

    def __unicode__(self):
        return self.name

    @classmethod
    def get_obj(self, app_name):
        app_obj = self.objects.filter(name=app_name)
        if app_obj.exists():
            return app_obj[0]
        else:
            app_obj = self.objects.create(name=app_name)
            return app_obj

class Calendar(models.Model):
    cdate = models.DateField()
    is_holiday = models.IntegerField(default = 2)

    def __unicode__(self):
        return self.cdate

    @classmethod
    def get_obj(self, cdate):
        cobj = self.objects.filter(cdate=cdate)
        if cobj.exists():
            return cobj[0]
        else:
            cobj = self.objects.create(cdate=cdate)
            return cobj

class BackupFile(models.Model):
    name = models.CharField(max_length=50)
    path = models.CharField(max_length=256)
    size = models.CharField(max_length=256)
    mtime = models.DateTimeField(null=True)
    ctime = models.DateTimeField(null=True)
    atime = models.DateTimeField(null=True)
    md5 = models.CharField(max_length=256)
    app = models.ForeignKey('App', null=True)
    backup_date = models.ForeignKey('Calendar', null=True)
    backup_time = models.TimeField(null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("path", "name"),)

    @classmethod
    def get_obj(self, path, filename):
        bkfile = self.objects.get(path=path, name=filename)
        return bkfile

    def update_obj(self, size, mtime, ctime, atime, md5, app_id, backup_date_id, backup_time):
        self.size=size
        self.mtime=mtime
        self.ctime=ctime
        self.atime=atime
        self.md5=md5
        self.app_id=app_id
        self.backup_date_id=backup_date_id
        self.backup_date_id=backup_date_id
        self.save()

class BackupFile_DataSource(models.Model):
    file = models.ForeignKey('BackupFile', null=True)
    datasorce = models.ForeignKey('DataSource', null=True)
    file_state = models.IntegerField()


class DataSource(models.Model):
    name = models.CharField(max_length=256)
    ip = models.GenericIPAddressField(protocol='ipv4')
    hostname = models.CharField(max_length=256)

    def __unicode__(self):
        return self.name
