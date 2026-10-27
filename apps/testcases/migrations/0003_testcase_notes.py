from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('testcases', '0002_initial')]

    operations = [
        migrations.AddField(
            model_name='testcase',
            name='notes',
            field=models.TextField(blank=True, verbose_name='备注'),
        ),
    ]
