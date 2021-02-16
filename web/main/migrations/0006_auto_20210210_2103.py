# Generated by Django 3.0.8 on 2021-02-10 21:03

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20201106_1656'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='archive',
            name='delivered_at',
        ),
        migrations.RemoveField(
            model_name='archive',
            name='jobid',
        ),
        migrations.RemoveField(
            model_name='archive',
            name='requested_at',
        ),
        migrations.RemoveField(
            model_name='archive',
            name='user',
        ),
        migrations.AddField(
            model_name='archive',
            name='download_expiration_timestamp',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='download_url',
            field=models.URLField(max_length=2100, null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='warc_size',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='CaptureJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requested_url', models.CharField(db_index=True, max_length=2100)),
                ('capture_oembed_view', models.BooleanField(default=False)),
                ('headless', models.BooleanField(default=True)),
                ('label', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(choices=[('pending', 'pending'), ('in_progress', 'in_progress'), ('completed', 'completed'), ('failed', 'failed'), ('invalid', 'invalid')], db_index=True, default='invalid', max_length=15)),
                ('message', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('human', models.BooleanField(default=False)),
                ('order', models.FloatField(db_index=True)),
                ('step_count', models.FloatField(default=0)),
                ('step_description', models.CharField(blank=True, max_length=255, null=True)),
                ('capture_start_time', models.DateTimeField(blank=True, null=True)),
                ('capture_end_time', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='capture_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='archive',
            name='capture_job',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='archive', to='main.CaptureJob'),
        ),
    ]