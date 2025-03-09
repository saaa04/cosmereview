# Generated by Django 5.1.2 on 2024-11-08 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cosmereview', '0010_searchhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='cosme',
            name='capacity',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='cosme',
            name='product_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cosme',
            name='reference_price',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cosme',
            name='release_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
