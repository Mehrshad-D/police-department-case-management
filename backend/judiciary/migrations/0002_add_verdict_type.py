# Generated manually for verdict_type (GUILTY/INNOCENT)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judiciary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='verdict',
            name='verdict_type',
            field=models.CharField(
                choices=[('guilty', 'Guilty'), ('innocent', 'Innocent')],
                default='guilty',
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name='verdict',
            name='title',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
