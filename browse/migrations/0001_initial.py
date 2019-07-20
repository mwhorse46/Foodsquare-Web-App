# Generated by Django 2.2.1 on 2019-07-20 19:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Ingredient',
                'verbose_name_plural': 'Ingredients',
            },
        ),
        migrations.CreateModel(
            name='IngredientList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ingr_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='browse.Ingredient')),
            ],
            options={
                'verbose_name': 'IngredientList',
                'verbose_name_plural': 'IngredientLists',
            },
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pkg_name', models.CharField(max_length=50)),
                ('for_n_persons', models.IntegerField(default=1)),
                ('price', models.IntegerField()),
                ('available', models.BooleanField(default=True)),
                ('image', models.ImageField(default='menu/default.png', upload_to='menu/')),
                ('details', models.CharField(blank=True, max_length=250)),
                ('category', models.CharField(max_length=50)),
                ('ingr_list', models.ManyToManyField(through='browse.IngredientList', to='browse.Ingredient')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Restaurant')),
            ],
            options={
                'verbose_name': 'Package',
                'verbose_name_plural': 'Packages',
            },
        ),
        migrations.AddField(
            model_name='ingredientlist',
            name='pack_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='browse.Package'),
        ),
    ]
