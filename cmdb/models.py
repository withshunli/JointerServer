# encoding: utf-8

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# 用于记录CMDB查询、修改、操作事件日志
class EventLogs(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField(max_length=20)
    logs = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

# 记录服务器资产详细变更记录
class OptionLogs(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField(max_length=20)
    logs = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

# 服务器信息详细配置
class CmdbConf(models.Model):
    idc = models.CharField(max_length=20)
    ip = models.GenericIPAddressField(unique=True)
    owner = models.GenericIPAddressField(null=True)  # 如资产为虚拟机或Docker容器，该字段用于记录宿主机IP
    sn = models.CharField(max_length=15)
    anum = models.CharField(max_length=10,unique=True)
    type = models.CharField(max_length=15)
    model = models.CharField(max_length=30,null=True)
    cpu = models.CharField(max_length=30,null=True)
    mem = models.CharField(max_length=30,null=True)
    disk = models.CharField(max_length=30,null=True)
    position = models.CharField(max_length=30,null=True)
    op = models.CharField(max_length=30)
    rd = models.CharField(max_length=30)
    dept = models.CharField(max_length=30,null=True)
    useTime = models.DateTimeField(auto_now_add=True)
    useReason = models.CharField(max_length=50,null=True)
    attribute = models.CharField(max_length=50,null=True)
    remark = models.CharField(max_length=100,null=True)
    logs = models.ManyToManyField(OptionLogs)