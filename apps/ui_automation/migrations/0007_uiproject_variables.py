from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('ui_automation', '0006_scriptstep_structured_fields')]

    operations = [
        migrations.AddField(
            model_name='uiproject',
            name='variables',
            field=models.JSONField(blank=True, default=list, verbose_name='项目变量'),
        ),
    ]
