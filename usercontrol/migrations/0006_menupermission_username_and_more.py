# usercontrol/migrations/0006_fix_menupermission.py
#
# COMPLETE INSTRUCTIONS — do ALL of these steps:
#
# 1. In psql run:
#       ALTER TABLE usercontrol_menupermission DROP COLUMN IF EXISTS username;
#
# 2. Delete ALL existing 0006 migration files in usercontrol/migrations/:
#       0006_menupermission_username_and_more.py  (delete this)
#       0006_fix_menupermission.py                (if any old version exists, delete it too)
#
# 3. Place THIS file as usercontrol/migrations/0006_fix_menupermission.py
#
# 4. Run:
#       python manage.py migrate usercontrol 0005 --fake
#       python manage.py migrate usercontrol

from django.db import migrations


def delete_orphan_rows(apps, schema_editor):
    """Remove permission rows with no linked user."""
    schema_editor.execute(
        "DELETE FROM usercontrol_menupermission WHERE login_user_id IS NULL;"
    )


class Migration(migrations.Migration):

    dependencies = [
        ('usercontrol', '0005_alter_menupermission_table'),
    ]

    operations = [
        migrations.RunPython(
            delete_orphan_rows,
            reverse_code=migrations.RunPython.noop,
        ),
    ]