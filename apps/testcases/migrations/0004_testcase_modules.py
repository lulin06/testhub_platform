from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0002_initial'),
        ('testcases', '0003_testcase_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCaseModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='模块名称')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='testcases.testcasemodule', verbose_name='父模块')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testcase_modules', to='projects.project', verbose_name='所属项目')),
            ],
            options={
                'db_table': 'testcase_modules',
                'ordering': ['sort_order', 'name', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='testcasemodule',
            constraint=models.UniqueConstraint(fields=('project', 'parent', 'name'), name='unique_testcase_module_name_per_parent'),
        ),
        migrations.AddField(
            model_name='testcase',
            name='module',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='testcases', to='testcases.testcasemodule', verbose_name='用例模块'),
        ),
    ]
