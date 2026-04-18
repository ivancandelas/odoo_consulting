from odoo import _, api, fields, models


class MeetingMinuteCommitment(models.Model):
    _name = "meeting.minute.commitment"
    _description = "Compromiso de Acta de Reunión"
    _order = "meeting_id, sequence, id"
    _rec_name = "description"

    sequence = fields.Integer(string="Secuencia", default=10)
    meeting_id = fields.Many2one(
        "meeting.minute", string="Acta", required=True, ondelete="cascade", index=True,
    )
    description = fields.Text(string="Descripción", required=True)

    responsible_partner_id = fields.Many2one(
        "res.partner", string="Responsable",
        default=lambda self: self.env.user.partner_id,
        index=True,
        help="Persona o contacto realmente responsable del compromiso. "
             "Puede ser un empleado (con o sin usuario Odoo), un contacto "
             "del cliente, un proveedor o cualquier tercero.",
    )
    responsible_user_id = fields.Many2one(
        "res.users", string="Usuario interno",
        default=lambda self: self.env.user,
        index=True,
        help="Usuario Odoo que da seguimiento operativo al compromiso. "
             "Puede ser el mismo responsable (si tiene cuenta) o un "
             "responsable interno distinto. Se usa para asignar tareas "
             "y para el filtro 'Mis compromisos'.",
    )

    due_date = fields.Date(string="Fecha compromiso")
    state = fields.Selection(
        selection=[
            ("pending", "Pendiente"),
            ("in_progress", "En curso"),
            ("done", "Cumplido"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado", default="pending", required=True,
    )
    note = fields.Char(string="Observaciones")

    @api.depends("description")
    def _compute_display_name(self):
        for rec in self:
            first_line = (rec.description or "").splitlines()[0:1]
            summary = first_line[0].strip() if first_line else ""
            if len(summary) > 80:
                summary = summary[:77].rstrip() + "…"
            rec.display_name = summary or _("Compromiso")

    # ------------------------------------------------------------------
    # Sincronización suave entre responsable canónico y usuario interno
    # ------------------------------------------------------------------
    @api.onchange("responsible_partner_id")
    def _onchange_responsible_partner_id(self):
        """Si el partner tiene un único usuario interno y no hay usuario
        asignado, precargarlo. Sugerencia, no constraint."""
        if not self.responsible_partner_id:
            return
        if self.responsible_user_id:
            return
        user = self.env["res.users"].search([
            ("partner_id", "=", self.responsible_partner_id.id),
            ("share", "=", False),
            ("active", "=", True),
        ], limit=2)
        if len(user) == 1:
            self.responsible_user_id = user

    @api.onchange("responsible_user_id")
    def _onchange_responsible_user_id(self):
        """Si se elige un usuario interno y no hay partner canónico,
        heredarlo del usuario."""
        if self.responsible_user_id and not self.responsible_partner_id:
            self.responsible_partner_id = self.responsible_user_id.partner_id

    def action_mark_done(self):
        self.write({"state": "done"})

    def action_mark_cancelled(self):
        self.write({"state": "cancelled"})
