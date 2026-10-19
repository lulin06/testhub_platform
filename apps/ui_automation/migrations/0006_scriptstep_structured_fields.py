from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ui_automation', '0005_recorded_script_replay'),
    ]

    operations = [
        migrations.AddField(model_name='element', name='locator_options', field=models.JSONField(blank=True, default=dict, verbose_name='Playwright定位选项')),
        migrations.AddField(model_name='scriptstep', name='assert_type', field=models.CharField(blank=True, max_length=20, verbose_name='断言类型')),
        migrations.AddField(model_name='scriptstep', name='assert_value', field=models.TextField(blank=True, verbose_name='断言期望值')),
        migrations.AddField(model_name='scriptstep', name='input_value', field=models.TextField(blank=True, verbose_name='输入值')),
        migrations.AddField(model_name='scriptstep', name='raw_code', field=models.TextField(blank=True, verbose_name='原始代码')),
        migrations.AddField(model_name='scriptstep', name='source_line_end', field=models.IntegerField(blank=True, null=True, verbose_name='结束代码行')),
        migrations.AddField(model_name='scriptstep', name='source_line_start', field=models.IntegerField(blank=True, null=True, verbose_name='起始代码行')),
        migrations.AddField(model_name='scriptstep', name='wait_time', field=models.IntegerField(default=1000, verbose_name='等待时间(毫秒)')),
        migrations.AlterField(
            model_name='scriptstep', name='action_type',
            field=models.CharField(choices=[('CLICK', '点击'), ('INPUT', '输入'), ('PRESS', '按键'), ('SELECT', '选择'), ('CHECK', '勾选'), ('UNCHECK', '取消勾选'), ('GETTEXT', '获取文本'), ('WAITFOR', '等待元素'), ('VERIFY', '验证'), ('WAIT', '等待'), ('HOVER', '悬停'), ('SCROLL', '滚动'), ('NAVIGATE', '导航'), ('SCREENSHOT', '截图'), ('SWITCH_TAB', '切换标签页'), ('CUSTOM', '自定义')], max_length=20, verbose_name='操作类型'),
        ),
        migrations.AlterField(
            model_name='testcasestep', name='action_type',
            field=models.CharField(choices=[('click', '点击'), ('fill', '输入文本'), ('press', '按键'), ('select', '选择选项'), ('check', '勾选'), ('uncheck', '取消勾选'), ('getText', '获取文本'), ('waitFor', '等待元素'), ('hover', '悬停'), ('scroll', '滚动'), ('screenshot', '截图'), ('assert', '断言'), ('wait', '等待'), ('switchTab', '切换标签页'), ('navigate', '跳转URL')], max_length=20, verbose_name='操作类型'),
        ),
    ]
