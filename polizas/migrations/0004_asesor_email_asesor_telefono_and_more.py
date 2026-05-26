from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polizas', '0003_poliza_fecha_pago_contado'),
    ]

    operations = [
        migrations.AddField(
            model_name='asesor',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='asesor',
            name='telefono',
            field=models.CharField(blank=True, max_length=30, verbose_name='Teléfono'),
        ),
        migrations.AddField(
            model_name='companiaaseguradora',
            name='contacto',
            field=models.CharField(blank=True, max_length=150, verbose_name='Contacto'),
        ),
        migrations.AddField(
            model_name='companiaaseguradora',
            name='telefono',
            field=models.CharField(blank=True, max_length=30, verbose_name='Teléfono'),
        ),
    ]
