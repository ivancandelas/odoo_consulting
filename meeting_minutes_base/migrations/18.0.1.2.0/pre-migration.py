"""Renombra la columna `responsible_id` → `responsible_user_id`.

Se ejecuta antes de que el ORM cargue el módulo actualizado, para que Odoo
encuentre la columna con el nuevo nombre y no intente recrearla (lo que
perdería los datos). El tipo FK no cambia (ambos apuntan a `res.users`).
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'meeting_minute_commitment'
          AND column_name IN ('responsible_id', 'responsible_user_id')
        """
    )
    existing = {row[0] for row in cr.fetchall()}
    if "responsible_id" in existing and "responsible_user_id" not in existing:
        cr.execute(
            "ALTER TABLE meeting_minute_commitment "
            "RENAME COLUMN responsible_id TO responsible_user_id"
        )
