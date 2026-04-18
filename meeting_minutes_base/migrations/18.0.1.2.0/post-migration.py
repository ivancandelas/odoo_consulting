"""Pobla `responsible_partner_id` a partir del usuario histórico.

Para cada compromiso sin `responsible_partner_id`, lo asigna al partner
del usuario interno `responsible_user_id`. Es una heurística razonable:
en el modelo antiguo el único responsable posible era un `res.users`, así
que su partner es el responsable canónico en el nuevo modelo.
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """
        UPDATE meeting_minute_commitment AS c
        SET responsible_partner_id = u.partner_id
        FROM res_users AS u
        WHERE c.responsible_user_id = u.id
          AND c.responsible_partner_id IS NULL
        """
    )
    env["meeting.minute.commitment"].invalidate_model(["responsible_partner_id"])
