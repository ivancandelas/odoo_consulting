"""Migración post-update para el rediseño de trazabilidad.

Compatibilidad con datos existentes (<= 18.0.1.0.x):

1. Las actas creadas con `action_create_next_meeting` ya dejaban
   `parent_meeting_id` seteado en la hija, así que `child_meeting_ids`
   ya funciona sin tocar datos.

2. Para esas hijas históricas asignamos un `follow_up_type` por defecto
   de "internal_followup" — sólo si no lo tienen ya. Es informativo;
   el usuario puede reclasificar manualmente.

3. Los campos `next_meeting_*` quedan intactos. El formulario los
   expone como grupo "Legado" únicamente cuando tienen valor.

4. Disparamos el recómputo de `root_meeting_id` sobre todo el modelo
   para poblar el nuevo campo stored en registros existentes.
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    Meeting = env["meeting.minute"]

    derived_without_type = Meeting.search([
        ("parent_meeting_id", "!=", False),
        ("follow_up_type", "=", False),
    ])
    if derived_without_type:
        derived_without_type.write({"follow_up_type": "internal_followup"})

    all_meetings = Meeting.search([])
    if all_meetings:
        all_meetings._compute_root_meeting_id()
        all_meetings.flush_recordset(["root_meeting_id"])
