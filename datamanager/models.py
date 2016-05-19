from django.db import models

# Create your models here.

from django.db import models

# Create your models here.
class appinfo_table(models.Model):
    full_name = models.CharField(max_length=40)
    name = models.CharField(max_length=10)
    ip = models.GenericIPAddressField(protocol='ipv4')

class createdate_table(models.Model):
    cdate = models.DateField()

class backupfileinfo_table(models.Model):
    name = models.CharField(max_length=30)
    size = models.CharField(max_length=256)
    mtime = models.DateTimeField(null=True)
    ctime = models.DateTimeField(null=True)
    atime = models.DateTimeField(null=True)
    md5 = models.CharField(max_length=30)
    app = models.ForeignKey('appinfo_table', null=True)
    cdate = models.ForeignKey('createdate_table', null=True)

