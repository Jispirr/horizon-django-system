from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0012_brand_category_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='brands/'),
        ),
        # Seed logo paths for the 7 built-in brands using already-copied files
        migrations.RunSQL(
            sql="""
            UPDATE horizon_brand SET logo = 'brands/bmw.png'           WHERE slug = 'bmw';
            UPDATE horizon_brand SET logo = 'brands/mercedes-benz.png' WHERE slug = 'mercedes-benz';
            UPDATE horizon_brand SET logo = 'brands/toyota.png'        WHERE slug = 'toyota';
            UPDATE horizon_brand SET logo = 'brands/tesla.png'         WHERE slug = 'tesla';
            UPDATE horizon_brand SET logo = 'brands/porsche.png'       WHERE slug = 'porsche';
            UPDATE horizon_brand SET logo = 'brands/lexus.png'         WHERE slug = 'lexus';
            UPDATE horizon_brand SET logo = 'brands/foton.png'         WHERE slug = 'foton';
            """,
            reverse_sql="""
            UPDATE horizon_brand SET logo = NULL;
            """,
        ),
    ]

