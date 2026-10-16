from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('perf_testing', '0010_perfcomparisonreport'), ('projects', '0003_project_center_fields')]

    operations = [
        migrations.AddField('perfproject', 'workspace_project', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='perf_project', to='projects.project', verbose_name='统一项目')),
        migrations.AddField('perfproject', 'is_deleted', models.BooleanField(db_comment='是否删除', default=False, verbose_name='是否删除')),
        migrations.AddField('perfproject', 'deleted_at', models.DateTimeField(blank=True, db_comment='删除时间', null=True, verbose_name='删除时间')),
        migrations.AddField('perfproject', 'deleted_by', models.ForeignKey(blank=True, db_comment='删除人', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_perf_projects', to='users.user', verbose_name='删除人')),
    ]
