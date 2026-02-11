from django.db import migrations


def normalize_word_unit_type_to_vocabulary(apps, schema_editor):
    Unit = apps.get_model('learning', 'Unit')
    Unit.objects.filter(unit_type='word').update(unit_type='vocabulary')


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0005_delete_bookset_delete_booksetunit_and_more'),
    ]

    operations = [
        migrations.RunPython(
            normalize_word_unit_type_to_vocabulary,
            migrations.RunPython.noop,
        ),
    ]
