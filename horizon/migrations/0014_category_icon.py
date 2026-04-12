from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0013_brand_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to='categories/'),
        ),
        migrations.RunSQL(
            sql="""
            UPDATE horizon_category SET icon = 'categories/sedan.svg'    WHERE slug = 'sedan';
            UPDATE horizon_category SET icon = 'categories/suv.svg'      WHERE slug = 'suv';
            UPDATE horizon_category SET icon = 'categories/sports.svg'   WHERE slug = 'sports';
            UPDATE horizon_category SET icon = 'categories/electric.svg' WHERE slug = 'electric';
            UPDATE horizon_category SET icon = 'categories/truck.svg'    WHERE slug = 'truck';
            UPDATE horizon_category SET icon = 'categories/van-mpv.svg'  WHERE slug = 'van-mpv';
            UPDATE horizon_category SET icon = 'categories/crossover.svg' WHERE slug = 'crossover';
            UPDATE horizon_category SET icon = 'categories/pickup.svg'   WHERE slug = 'pickup';
            """,
            reverse_sql="UPDATE horizon_category SET icon = NULL;",
        ),
    ]
