from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('api_testing', '0002_initial'), ('projects', '0003_project_center_fields')]

    operations = [
        migrations.AddField('apiproject', 'workspace_project', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='api_project', to='projects.project', verbose_name='统一项目')),
        migrations.AddField('apiproject', 'is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
        migrations.AddField('apiproject', 'deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
        migrations.AddField('apiproject', 'deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_api_projects', to='users.user', verbose_name='删除人')),
    ]
