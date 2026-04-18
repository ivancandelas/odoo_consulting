from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class MeetingMinute(models.Model):
    _name = "meeting.minute"
    _description = "Acta de Reunión"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc, id desc"

    name = fields.Char(
        string="Folio",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nuevo"),
        tracking=True,
    )
    title = fields.Char(string="Título", required=True, tracking=True)
    location = fields.Char(string="Lugar")
    scheduled_date = fields.Datetime(
        string="Fecha programada", required=True, tracking=True,
        default=fields.Datetime.now,
    )
    duration = fields.Float(
        string="Duración prevista (h)", default=1.0,
        help="Duración estimada en horas. Se usa para el evento de calendario.",
    )
    objective = fields.Text(string="Objetivo")
    agenda = fields.Html(string="Agenda del día", sanitize=True)
    development_notes = fields.Html(
        string="Notas / Desarrollo de la reunión", sanitize=True,
        help="Narrativa de lo ocurrido durante la reunión: puntos tratados, "
             "avances, incidentes, decisiones parciales y comentarios. "
             "No se debe usar para acuerdos finales (ver Conclusiones).",
    )
    conclusions = fields.Html(
        string="Conclusiones", sanitize=True,
        help="Acuerdos finales, definiciones y resultado de la reunión. "
             "Para la narrativa de la sesión utilizar Notas / Desarrollo.",
    )

    start_real = fields.Datetime(string="Inicio real", readonly=True, copy=False, tracking=True)
    end_real = fields.Datetime(string="Fin real", readonly=True, copy=False, tracking=True)
    real_duration = fields.Float(
        string="Duración real (h)",
        compute="_compute_real_duration", store=True,
    )

    partner_id = fields.Many2one("res.partner", string="Cliente", tracking=True)
    user_id = fields.Many2one(
        "res.users", string="Responsable",
        default=lambda self: self.env.user, tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía",
        default=lambda self: self.env.company, required=True,
    )

    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("scheduled", "Programada"),
            ("in_progress", "En curso"),
            ("done", "Finalizada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado", default="draft", required=True, tracking=True, copy=False,
    )

    attendee_ids = fields.One2many(
        "meeting.minute.attendee", "meeting_id", string="Asistentes",
        copy=True,
    )
    attendee_count = fields.Integer(
        string="# Asistentes", compute="_compute_attendee_count",
    )
    commitment_ids = fields.One2many(
        "meeting.minute.commitment", "meeting_id", string="Compromisos",
        copy=True,
    )
    commitment_count = fields.Integer(
        string="# Compromisos", compute="_compute_commitment_count",
    )

    # ------------------------------------------------------------------
    # Trazabilidad entre reuniones (rediseño 18.0.1.1.0)
    # ------------------------------------------------------------------
    parent_meeting_id = fields.Many2one(
        "meeting.minute", string="Reunión origen", copy=False,
        ondelete="set null", index=True, tracking=True,
        help="Reunión desde la que se derivó esta. Una reunión puede "
             "tener varias derivadas (1:N), pero sólo un origen.",
    )
    child_meeting_ids = fields.One2many(
        "meeting.minute", "parent_meeting_id", string="Reuniones derivadas",
        copy=False,
    )
    root_meeting_id = fields.Many2one(
        "meeting.minute", string="Reunión raíz del hilo",
        compute="_compute_root_meeting_id", store=True, index=True,
        recursive=True,
    )
    follow_up_type = fields.Selection(
        selection=[
            ("technical", "Técnica"),
            ("commercial", "Comercial"),
            ("validation", "Validación"),
            ("internal_followup", "Seguimiento interno"),
            ("other", "Otro"),
        ],
        string="Tipo de seguimiento", copy=False, tracking=True,
        help="Clasifica por qué se creó esta reunión como derivada de "
             "otra. Las reuniones raíz (sin origen) no suelen tenerlo.",
    )
    follow_up_count = fields.Integer(
        string="# Seguimientos", compute="_compute_follow_up_count",
    )
    related_meeting_count = fields.Integer(
        string="# Reuniones relacionadas", compute="_compute_follow_up_count",
    )

    # ------------------------------------------------------------------
    # Campos LEGADO — mantenidos por compatibilidad con datos existentes.
    # No usar en lógica nueva; reemplazados por child_meeting_ids + wizard.
    # ------------------------------------------------------------------
    next_meeting_id = fields.Many2one(
        "meeting.minute", string="Siguiente reunión (legado)", readonly=True, copy=False,
        ondelete="set null",
        help="DEPRECADO desde 18.0.1.1.0. Use 'Reuniones derivadas'. "
             "Se conserva para acceder a datos históricos.",
    )
    next_meeting_date = fields.Datetime(
        string="Fecha próxima reunión (legado)",
        help="DEPRECADO desde 18.0.1.1.0. Cree reuniones derivadas en su lugar.",
    )
    next_meeting_location = fields.Char(
        string="Lugar próxima reunión (legado)",
        help="DEPRECADO desde 18.0.1.1.0.",
    )
    next_meeting_objective = fields.Text(
        string="Objetivo próxima reunión (legado)",
        help="DEPRECADO desde 18.0.1.1.0.",
    )
    has_legacy_next_meeting_data = fields.Boolean(
        compute="_compute_has_legacy_next_meeting_data",
    )

    _sql_constraints = [
        ("meeting_minute_name_uniq", "unique(name, company_id)",
         "El folio del acta debe ser único por compañía."),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("start_real", "end_real")
    def _compute_real_duration(self):
        for rec in self:
            if rec.start_real and rec.end_real and rec.end_real > rec.start_real:
                delta = rec.end_real - rec.start_real
                rec.real_duration = round(delta.total_seconds() / 3600.0, 2)
            else:
                rec.real_duration = 0.0

    @api.depends("attendee_ids")
    def _compute_attendee_count(self):
        for rec in self:
            rec.attendee_count = len(rec.attendee_ids)

    @api.depends("commitment_ids")
    def _compute_commitment_count(self):
        for rec in self:
            rec.commitment_count = len(rec.commitment_ids)

    @api.depends("child_meeting_ids", "parent_meeting_id")
    def _compute_follow_up_count(self):
        for rec in self:
            rec.follow_up_count = len(rec.child_meeting_ids)
            rec.related_meeting_count = (
                (1 if rec.parent_meeting_id else 0) + len(rec.child_meeting_ids)
            )

    @api.depends("parent_meeting_id", "parent_meeting_id.root_meeting_id")
    def _compute_root_meeting_id(self):
        for rec in self:
            if rec.parent_meeting_id:
                rec.root_meeting_id = (
                    rec.parent_meeting_id.root_meeting_id or rec.parent_meeting_id
                )
            else:
                rec.root_meeting_id = rec

    @api.depends(
        "next_meeting_id", "next_meeting_date",
        "next_meeting_location", "next_meeting_objective",
    )
    def _compute_has_legacy_next_meeting_data(self):
        for rec in self:
            rec.has_legacy_next_meeting_data = bool(
                rec.next_meeting_id
                or rec.next_meeting_date
                or rec.next_meeting_location
                or rec.next_meeting_objective
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("start_real", "end_real")
    def _check_real_times(self):
        for rec in self:
            if rec.end_real and not rec.start_real:
                raise ValidationError(_("No se puede registrar un fin real sin un inicio real."))
            if rec.start_real and rec.end_real and rec.end_real < rec.start_real:
                raise ValidationError(_("El fin real no puede ser anterior al inicio real."))

    @api.constrains("parent_meeting_id")
    def _check_parent_meeting_not_self(self):
        for rec in self:
            parent = rec.parent_meeting_id
            visited = set()
            while parent:
                if parent.id == rec.id:
                    raise ValidationError(_(
                        "Una reunión no puede ser origen (directo o indirecto) de sí misma."
                    ))
                if parent.id in visited:
                    break
                visited.add(parent.id)
                parent = parent.parent_meeting_id

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("Nuevo"):
                vals["name"] = self.env["ir.sequence"].next_by_code("meeting.minute") or _("Nuevo")
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_schedule(self):
        for rec in self:
            if rec.state not in ("draft", "cancelled"):
                raise UserError(_("Solo se puede programar una reunión en estado Borrador o Cancelada."))
            if not rec.scheduled_date:
                raise UserError(_("Debe indicar la fecha programada antes de programar la reunión."))
            rec.state = "scheduled"

    def action_start(self):
        for rec in self:
            if rec.state not in ("scheduled", "draft"):
                raise UserError(_("Solo se puede iniciar una reunión Programada o en Borrador."))
            rec.write({
                "state": "in_progress",
                "start_real": fields.Datetime.now(),
            })

    def action_finish(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(_("Solo se puede finalizar una reunión que está En curso."))
            if not rec.start_real:
                raise UserError(_("No se puede finalizar una reunión sin inicio real registrado."))
            rec.write({
                "state": "done",
                "end_real": fields.Datetime.now(),
            })

    def action_cancel(self):
        for rec in self:
            if rec.state == "done":
                raise UserError(_("No se puede cancelar un acta ya finalizada."))
            rec.state = "cancelled"

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"

    # ------------------------------------------------------------------
    # Seguimientos / trazabilidad
    # ------------------------------------------------------------------
    def action_open_follow_up_wizard(self):
        """Abre el wizard para crear una reunión derivada tipificada."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Nueva reunión de seguimiento"),
            "res_model": "meeting.minute.follow.up.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_source_meeting_id": self.id},
        }

    def action_create_next_meeting(self):
        """DEPRECADO: delega en el nuevo wizard de seguimiento.

        Se conserva el nombre público para que llamadas existentes (botones
        en vistas heredadas por terceros, scripts) sigan funcionando.
        """
        return self.action_open_follow_up_wizard()

    def action_view_follow_ups(self):
        """Smart-button: muestra reuniones derivadas directas."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reuniones derivadas"),
            "res_model": "meeting.minute",
            "view_mode": "list,form,calendar",
            "domain": [("parent_meeting_id", "=", self.id)],
            "context": {
                "default_parent_meeting_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def _get_thread_meeting_ids(self):
        """Devuelve los ids de toda la rama (raíz + descendientes) usando CTE."""
        self.ensure_one()
        root_id = self.root_meeting_id.id or self.id
        self.env.cr.execute(
            """
            WITH RECURSIVE thread(id) AS (
                SELECT id FROM meeting_minute WHERE id = %s
                UNION
                SELECT m.id
                FROM meeting_minute m
                JOIN thread t ON m.parent_meeting_id = t.id
            )
            SELECT id FROM thread
            """,
            (root_id,),
        )
        return [row[0] for row in self.env.cr.fetchall()]

    def action_view_thread(self):
        """Acción: muestra todo el hilo (raíz + descendientes) de esta reunión."""
        self.ensure_one()
        ids = self._get_thread_meeting_ids()
        return {
            "type": "ir.actions.act_window",
            "name": _("Hilo de reuniones"),
            "res_model": "meeting.minute",
            "view_mode": "list,form,calendar",
            "domain": [("id", "in", ids)],
            "context": {
                "search_default_group_root": 1,
            },
        }
