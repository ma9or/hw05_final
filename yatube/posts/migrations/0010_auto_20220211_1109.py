# Generated by Django 2.2.16 on 2022-02-11 11:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20220211_0610'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='unique_author_user_following',
        ),
    ]
