from datetime import timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MeetingMinuteFollowUpWizard(models.TransientModel):
    _name = "meeting.minute.follow.up.wizard"
    _description = "Asistente: Crear reunión de seguimiento"

    source_meeting_id = fields.Many2one(
        "meeting.minute", string="Reunión origen",
        required=True, readonly=True, ondelete="cascade",
    )
    source_partner_id = fields.Many2one(
        related="source_meeting_id.partner_id", readonly=True,
    )
    follow_up_type = fields.Selection(
        selection=[
            ("technical", "Técnica"),
            ("commercial", "Comercial"),
            ("validation", "Validación"),
            ("internal_followup", "Seguimiento interno"),
            ("other", "Otro"),
        ],
        string="Tipo de seguimiento", required=True, default="internal_followup",
    )
    title = fields.Char(string="Título de la nueva reunión", required=True)
    scheduled_date = fields.Datetime(string="Fecha programada", required=True)
    duration = fields.Float(string="Duración prevista (h)", default=1.0)
    location = fields.Char(string="Lugar")
    objective = fields.Text(string="Objetivo")
    user_id = fields.Many2one(
        "res.users", string="Responsable",
        default=lambda self: self.env.user, required=True,
    )

    copy_attendees = fields.Boolean(
        string="Copiar asistentes de la reunión origen", default=True,
    )
    copy_pending_commitments = fields.Boolean(
        string="Arrastrar compromisos pendientes", default=False,
        help="Crea en la nueva reunión una copia de los compromisos en "
             "estado pendiente / en progreso, para darles continuidad.",
    )
    open_after_create = fields.Boolean(
        string="Abrir nueva reunión al crearla", default=True,
    )

    @api.onchange("source_meeting_id", "follow_up_type")
    def _onchange_defaults_from_source(self):
        """Sugiere título, fecha y lugar a partir del acta origen."""
        if not self.source_meeting_id:
            return
        source = self.source_meeting_id
        type_labels = dict(self._fields["follow_up_type"].selection)
        label = type_labels.get(self.follow_up_type or "internal_followup", "")
        if not self.title:
            self.title = (
                "%s - %s" % (source.title, label) if label else source.title
            )
        if not self.location:
            self.location = source.location
        if not self.objective:
            self.objective = source.objective
        if not self.scheduled_date:
            base = source.scheduled_date or fields.Datetime.now()
            self.scheduled_date = base + timedelta(days=7)

    def action_create_follow_up(self):
        self.ensure_one()
        source = self.source_meeting_id
        if not source:
            raise UserError(_("La reunión origen ya no está disponible."))

        default_vals = {
            "title": self.title,
            "scheduled_date": self.scheduled_date,
            "duration": self.duration or 1.0,
            "location": self.location or False,
            "objective": self.objective or False,
            "user_id": self.user_id.id,
            "parent_meeting_id": source.id,
            "follow_up_type": self.follow_up_type,
            "state": "draft",
            "start_real": False,
            "end_real": False,
            "agenda": False,
            "development_notes": False,
            "conclusions": False,
            "next_meeting_id": False,
            "next_meeting_date": False,
            "next_meeting_location": False,
            "next_meeting_objective": False,
        }
        if not self.copy_attendees:
            default_vals["attendee_ids"] = []
        default_vals["commitment_ids"] = []

        new_meeting = source.copy(default=default_vals)

        if self.copy_pending_commitments:
            for commitment in source.commitment_ids.filtered(
                lambda c: c.state in ("pending", "in_progress")
            ):
                commitment.copy(default={
                    "meeting_id": new_meeting.id,
                    "state": "pending",
                })

        source.message_post(body=Markup(_(
            "Se creó la reunión de seguimiento <b>%(name)s</b> (%(ftype)s).",
        )) % {
            "name": new_meeting.name,
            "ftype": dict(self._fields["follow_up_type"].selection).get(
                self.follow_up_type, self.follow_up_type,
            ),
        })
        new_meeting.message_post(body=Markup(_(
            "Reunión creada como seguimiento de <b>%s</b>.",
        )) % source.name)

        if not self.open_after_create:
            return {"type": "ir.actions.act_window_close"}
        return {
            "type": "ir.actions.act_window",
            "name": _("Reunión de seguimiento"),
            "res_model": "meeting.minute",
            "res_id": new_meeting.id,
            "view_mode": "form",
            "target": "current",
        }
