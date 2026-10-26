from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui_automation', '0010_uischeduledtask_storage_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scriptstep',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('CLICK', '点击'), ('INPUT', '输入'), ('PRESS', '按键'), ('SELECT', '选择'),
                    ('CHECK', '勾选'), ('UNCHECK', '取消勾选'), ('GETTEXT', '获取文本'),
                    ('WAITFOR', '等待元素'), ('VERIFY', '验证'), ('WAIT', '等待'), ('HOVER', '悬停'),
                    ('SCROLL', '滚动'), ('NAVIGATE', '导航'), ('SCREENSHOT', '截图'),
                    ('SWITCH_TAB', '切换标签页'), ('STORAGE_STATE', '登录态'), ('CUSTOM', '自定义'),
                ],
                max_length=20,
                verbose_name='操作类型',
            ),
        ),
    ]
