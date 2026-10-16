from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('ui_automation', '0002_initial'), ('projects', '0003_project_center_fields')]

    operations = [
        migrations.AddField('uiproject', 'workspace_project', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ui_project', to='projects.project', verbose_name='统一项目')),
        migrations.AddField('uiproject', 'is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
        migrations.AddField('uiproject', 'deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
        migrations.AddField('uiproject', 'deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_ui_projects', to='users.user', verbose_name='删除人')),
    ]
