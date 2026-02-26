# Generated migration for evidence spec: witness media, biological verification, vehicle fields, ID owner

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_validity_to_verification_status(apps, schema_editor):
    BiologicalEvidence = apps.get_model('evidence', 'BiologicalEvidence')
    for row in BiologicalEvidence.objects.all():
        if row.validity_status == 'approved':
            row.verification_status = 'verified_forensic'
        elif row.validity_status == 'rejected':
            row.verification_status = 'rejected'
        else:
            row.verification_status = 'pending'
        row.save()


def copy_vehicle_legacy_fields(apps, schema_editor):
    VehicleEvidence = apps.get_model('evidence', 'VehicleEvidence')
    for row in VehicleEvidence.objects.all():
        row.model = row.make_model or ''
        row.license_plate = row.plate_number or ''
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('evidence', '0001_initial'),
    ]

    operations = [
        # Evidence: remove date_recorded (use created_at only)
        migrations.RemoveField(model_name='evidence', name='date_recorded'),
        migrations.AlterModelOptions(
            name='evidence',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Evidence'},
        ),
        # WitnessEvidence: add transcript
        migrations.AddField(
            model_name='witnessevidence',
            name='transcript',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        # WitnessMedia: new model for multiple media files
        migrations.CreateModel(
            name='WitnessMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='evidence/witness/media/')),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video'), ('audio', 'Audio')], max_length=16)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('witness_evidence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='evidence.witnessevidence')),
            ],
        ),
        # BiologicalEvidence: add verification_result, verification_status; then migrate and remove old fields
        migrations.AddField(
            model_name='biologicalevidence',
            name='verification_result',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='biologicalevidence',
            name='verification_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('verified_forensic', 'Verified (Forensic)'),
                    ('verified_national_db', 'Verified (National DB)'),
                    ('rejected', 'Rejected'),
                ],
                default='pending',
                max_length=32,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copy_validity_to_verification_status, migrations.RunPython.noop),
        migrations.RemoveField(model_name='biologicalevidence', name='validity_status'),
        migrations.RemoveField(model_name='biologicalevidence', name='lab_results'),
        # VehicleEvidence: add model, color, license_plate; then migrate and remove make_model, plate_number
        migrations.AddField(
            model_name='vehicleevidence',
            name='model',
            field=models.CharField(blank=True, max_length=128, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vehicleevidence',
            name='color',
            field=models.CharField(blank=True, max_length=64, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vehicleevidence',
            name='license_plate',
            field=models.CharField(blank=True, max_length=32, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(copy_vehicle_legacy_fields, migrations.RunPython.noop),
        migrations.RemoveField(model_name='vehicleevidence', name='make_model'),
        migrations.RemoveField(model_name='vehicleevidence', name='plate_number'),
        # IDDocumentEvidence: add owner_full_name
        migrations.AddField(
            model_name='iddocumentevidence',
            name='owner_full_name',
            field=models.CharField(blank=True, max_length=255, default=''),
            preserve_default=False,
        ),
    ]
