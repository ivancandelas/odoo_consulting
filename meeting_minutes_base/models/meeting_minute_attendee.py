from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MeetingMinuteAttendee(models.Model):
    _name = "meeting.minute.attendee"
    _description = "Asistente de Acta de Reunión"
    _order = "meeting_id, sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    meeting_id = fields.Many2one(
        "meeting.minute", string="Acta", required=True, ondelete="cascade", index=True,
    )
    partner_id = fields.Many2one(
        "res.partner", string="Convocado", required=True, ondelete="restrict",
    )
    partner_company_id = fields.Many2one(
        "res.partner", string="Empresa",
        compute="_compute_partner_company", store=True, readonly=False,
        help="Empresa a la que pertenece el convocado.",
    )
    attendance_type = fields.Selection(
        selection=[
            ("onsite", "Presencial"),
            ("remote", "Remoto"),
            ("delegate", "Mandó a alguien"),
        ],
        string="Tipo de asistencia", required=True, default="onsite",
    )
    delegate_partner_id = fields.Many2one(
        "res.partner", string="Representado por",
        help="Persona que asistió en representación del convocado.",
    )
    attended = fields.Boolean(string="Asistió", default=True)
    note = fields.Char(string="Observaciones")

    @api.depends("partner_id")
    def _compute_partner_company(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.parent_id:
                rec.partner_company_id = rec.partner_id.parent_id
            elif rec.partner_id and rec.partner_id.is_company:
                rec.partner_company_id = rec.partner_id
            else:
                rec.partner_company_id = rec.partner_company_id

    @api.constrains("attendance_type", "delegate_partner_id")
    def _check_delegate(self):
        for rec in self:
            if rec.attendance_type == "delegate" and not rec.delegate_partner_id:
                raise ValidationError(_(
                    "Si marca 'Mandó a alguien' debe indicar quién asistió en representación."
                ))

    @api.onchange("attendance_type")
    def _onchange_attendance_type(self):
        if self.attendance_type != "delegate":
            self.delegate_partner_id = False
