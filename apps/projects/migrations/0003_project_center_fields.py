from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('projects', '0002_initial')]

    operations = [
        migrations.AddField('project', 'modules', models.JSONField(blank=True, default=list, verbose_name='关联模块')),
        migrations.AddField('project', 'is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
        migrations.AddField('project', 'deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
        migrations.AddField('project', 'deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_projects', to='users.user', verbose_name='删除人')),
    ]
