from django.db import migrations, models


class Migration(migrations.Migration):
    """Add Slack Incoming Webhook as a unified notification platform."""

    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unifiednotificationconfig',
            name='config_type',
            field=models.CharField(
                choices=[
                    ('webhook_feishu', '飞书机器人'),
                    ('webhook_wechat', '企业微信机器人'),
                    ('webhook_dingtalk', '钉钉机器人'),
                    ('webhook_slack', 'Slack 机器人'),
                ],
                default='webhook_feishu',
                max_length=20,
                verbose_name='配置类型',
            ),
        ),
        migrations.AlterField(
            model_name='unifiednotificationconfig',
            name='webhook_bots',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='飞书、企微、钉钉、Slack 机器人配置',
                null=True,
                verbose_name='Webhook机器人配置',
            ),
        ),
    ]
