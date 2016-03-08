# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CmdbConf',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('idc', models.CharField(max_length=20)),
                ('ip', models.GenericIPAddressField(unique=True)),
                ('owner', models.GenericIPAddressField()),
                ('sn', models.CharField(max_length=15)),
                ('anum', models.CharField(unique=True, max_length=10)),
                ('type', models.CharField(max_length=15)),
                ('model', models.CharField(max_length=30, null=True)),
                ('cpu', models.CharField(max_length=30, null=True)),
                ('mem', models.CharField(max_length=30, null=True)),
                ('disk', models.CharField(max_length=30, null=True)),
                ('position', models.CharField(max_length=30, null=True)),
                ('op', models.CharField(max_length=30)),
                ('rd', models.CharField(max_length=30)),
                ('dept', models.CharField(max_length=30, null=True)),
                ('useTime', models.DateTimeField(auto_now_add=True)),
                ('useReason', models.CharField(max_length=50, null=True)),
                ('attribute', models.CharField(max_length=50, null=True)),
                ('remark', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EventLogs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=20)),
                ('logs', models.CharField(max_length=100)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OptionLogs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=20)),
                ('logs', models.CharField(max_length=100)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='cmdbconf',
            name='logs',
            field=models.ManyToManyField(to='cmdb.OptionLogs'),
        ),
    ]
