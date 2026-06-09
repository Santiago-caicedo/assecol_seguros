from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polizas', '0004_asesor_email_asesor_telefono_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poliza',
            name='modo_pago',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente por definir'),
                    ('CONTADO', 'De Contado'),
                    ('CREDITO', 'A Crédito'),
                    ('MENSUAL', 'Pago Mensual'),
                    ('FINANCIADO', 'Financiado'),
                ],
                default='CONTADO',
                max_length=10,
                verbose_name='Modalidad de Pago',
            ),
        ),
    ]
