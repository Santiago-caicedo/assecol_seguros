from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polizas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poliza',
            name='financiera',
            field=models.CharField(blank=True, help_text='Solo aplica si la modalidad es Financiado.', max_length=150, verbose_name='Financiera'),
        ),
        migrations.AddField(
            model_name='poliza',
            name='numero_credito',
            field=models.CharField(blank=True, help_text='Solo aplica si la modalidad es Financiado.', max_length=50, verbose_name='Número de Crédito'),
        ),
        migrations.AlterField(
            model_name='poliza',
            name='modo_pago',
            field=models.CharField(
                choices=[
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
