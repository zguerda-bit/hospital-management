import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_rename_date_action_traceaction_timestamp_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Reste_token',
            new_name='ResetToken',
        ),
        migrations.RemoveField(
            model_name='patients',
            name='insurance',
        ),
        migrations.RemoveField(
            model_name='patients',
            name='nom_parent',
        ),
        migrations.RemoveField(
            model_name='patients',
            name='phn',
        ),
        migrations.RemoveField(
            model_name='patients',
            name='tel_parent',
        ),
        migrations.RemoveField(
            model_name='patients',
            name='user',
        ),
        migrations.RemoveField(
            model_name='specialty',
            name='description',
        ),
        migrations.AddField(
            model_name='patients',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='patients',
            name='first_name',
            field=models.CharField(default='Unknown', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='patients',
            name='gender',
            field=models.CharField(choices=[('M', 'Masculin'), ('F', 'Féminin')], default='M', max_length=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='patients',
            name='last_name',
            field=models.CharField(default='Unknown', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='patients',
            name='parent',
            field=models.ForeignKey(
                null=True,
                blank=True,
                default=None,
                limit_choices_to={'role': 'PARENT'},
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='traceaction',
            name='table_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='users',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Administrateur'), ('DOCTOR', 'Médecin'), ('PARENT', 'Parent')], max_length=15),
        ),
        migrations.DeleteModel(
            name='Appointment',
        ),
    ]