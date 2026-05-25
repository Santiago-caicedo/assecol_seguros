from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polizas', '0002_poliza_financiera_poliza_numero_credito_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='poliza',
            name='fecha_pago_contado',
            field=models.DateField(blank=True, help_text='Solo aplica si la modalidad es De Contado.', null=True, verbose_name='Fecha de Pago'),
        ),
    ]
