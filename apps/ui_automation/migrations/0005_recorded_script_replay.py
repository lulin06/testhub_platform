from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ui_automation', '0004_alter_testcasestep_action_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testscript',
            name='analysis',
            field=models.JSONField(blank=True, default=dict, verbose_name='脚本分析结果'),
        ),
        migrations.AddField(
            model_name='testscript',
            name='recording_config',
            field=models.JSONField(blank=True, default=dict, verbose_name='录制配置'),
        ),
        migrations.AddField(
            model_name='testscript',
            name='source',
            field=models.CharField(choices=[('manual', '手工创建'), ('recorded', 'Playwright录制'), ('imported', '导入')], default='manual', max_length=20, verbose_name='脚本来源'),
        ),
        migrations.AddField(
            model_name='testscript',
            name='start_url',
            field=models.URLField(blank=True, verbose_name='录制起始URL'),
        ),
        migrations.AddField(
            model_name='testexecution',
            name='artifact_manifest',
            field=models.JSONField(blank=True, default=list, verbose_name='执行产物'),
        ),
        migrations.AddField(
            model_name='testexecution',
            name='execution_logs',
            field=models.TextField(blank=True, verbose_name='执行日志'),
        ),
        migrations.AddField(
            model_name='testexecution',
            name='execution_type',
            field=models.CharField(choices=[('legacy', '传统执行'), ('recorded_script', '录制脚本回放')], default='legacy', max_length=30, verbose_name='执行类型'),
        ),
        migrations.AddField(
            model_name='testexecution',
            name='run_config',
            field=models.JSONField(blank=True, default=dict, verbose_name='回放配置'),
        ),
    ]
