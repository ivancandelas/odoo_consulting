# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HourWalletAssignTimesheetsWizard(models.TransientModel):
    """Asistente para vincular timesheets existentes a una bolsa.

    Flujo:
      1. Se abre desde el botón "Asignar timesheets" de la bolsa.
      2. Los filtros (fechas, empleados, tareas) acotan los candidatos.
         Por defecto se muestra el último mes.
      3. Solo se listan timesheets **sin bolsa asignada**; la reasignación
         entre bolsas está bloqueada a nivel de modelo
         (``_check_wallet_reassignment_allowed``).
      4. El usuario revisa/deselecciona y confirma la asignación en bloque.
    """

    _name = "hour.wallet.assign.timesheets.wizard"
    _description = "Asignar timesheets a bolsa de horas"

    wallet_id = fields.Many2one(
        "hour.wallet",
        string="Bolsa destino",
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        related="wallet_id.partner_id",
        readonly=True,
    )
    project_id = fields.Many2one(
        related="wallet_id.project_id",
        readonly=True,
    )
    wallet_state = fields.Selection(
        related="wallet_id.state",
        readonly=True,
    )
    hours_available = fields.Float(
        related="wallet_id.hours_available",
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Filtros server-side
    # ------------------------------------------------------------------
    date_from = fields.Date(
        string="Desde",
        required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=30),
    )
    date_to = fields.Date(
        string="Hasta",
        required=True,
        default=fields.Date.context_today,
    )
    restrict_to_project = fields.Boolean(
        string="Solo del proyecto de la bolsa",
        default=True,
        help="Si se desmarca, se consideran timesheets de cualquier proyecto "
             "del mismo cliente.",
    )
    user_ids = fields.Many2many(
        "res.users",
        "hour_wallet_assign_wizard_user_rel",
        "wizard_id",
        "user_id",
        string="Empleados",
    )
    task_ids = fields.Many2many(
        "project.task",
        "hour_wallet_assign_wizard_task_rel",
        "wizard_id",
        "task_id",
        string="Tareas",
    )

    # ------------------------------------------------------------------
    # Selección
    # ------------------------------------------------------------------
    line_ids = fields.Many2many(
        "account.analytic.line",
        "hour_wallet_assign_wizard_line_rel",
        "wizard_id",
        "line_id",
        string="Timesheets a asignar",
    )
    total_selected_hours = fields.Float(
        compute="_compute_total_selected_hours",
        digits=(12, 2),
    )

    # ==================================================================
    # COMPUTES
    # ==================================================================
    @api.depends("line_ids.unit_amount")
    def _compute_total_selected_hours(self):
        for wiz in self:
            wiz.total_selected_hours = sum(wiz.line_ids.mapped("unit_amount"))

    # ==================================================================
    # DEFAULTS / ONCHANGE
    # ==================================================================
    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        wallet_id = vals.get("wallet_id") or self.env.context.get(
            "default_wallet_id"
        )
        if wallet_id and "line_ids" in fields_list:
            wallet = self.env["hour.wallet"].browse(wallet_id)
            today = fields.Date.context_today(self)
            domain = self._initial_candidate_domain(
                wallet=wallet,
                date_from=vals.get("date_from") or (today - timedelta(days=30)),
                date_to=vals.get("date_to") or today,
                restrict_to_project=vals.get("restrict_to_project", True),
            )
            candidates = self.env["account.analytic.line"].search(domain)
            vals["line_ids"] = [(6, 0, candidates.ids)]
        return vals

    @api.model
    def _initial_candidate_domain(self, wallet, date_from, date_to,
                                   restrict_to_project):
        """Dominio equivalente a ``_build_candidate_domain`` pero para
        construir la selección inicial antes de que exista el registro
        del wizard (no hay ``user_ids``/``task_ids`` aún)."""
        domain = [
            ("hour_wallet_id", "=", False),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("project_id", "!=", False),
        ]
        if restrict_to_project and wallet.project_id:
            domain.append(("project_id", "=", wallet.project_id.id))
        elif wallet.partner_id:
            domain.append(("project_id.partner_id", "=", wallet.partner_id.id))
        return domain

    @api.onchange("task_ids")
    def _onchange_task_clamp_project(self):
        for wiz in self:
            if wiz.restrict_to_project and wiz.project_id and wiz.task_ids:
                wiz.task_ids = wiz.task_ids.filtered(
                    lambda t: t.project_id == wiz.project_id
                )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wiz in self:
            if wiz.date_from and wiz.date_to and wiz.date_to < wiz.date_from:
                raise ValidationError(
                    _("La fecha 'Hasta' no puede ser anterior a la fecha 'Desde'.")
                )

    # ==================================================================
    # CANDIDATOS
    # ==================================================================
    def _build_candidate_domain(self):
        """Construye el dominio de búsqueda de timesheets candidatos."""
        self.ensure_one()
        domain = [
            ("hour_wallet_id", "=", False),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("project_id", "!=", False),
        ]
        if self.restrict_to_project and self.project_id:
            domain.append(("project_id", "=", self.project_id.id))
        elif self.partner_id:
            # Sin restricción a un proyecto, se acota al partner de la bolsa.
            domain.append(("project_id.partner_id", "=", self.partner_id.id))
        if self.user_ids:
            domain.append(("user_id", "in", self.user_ids.ids))
        if self.task_ids:
            domain.append(("task_id", "in", self.task_ids.ids))
        return domain

    def _search_candidates(self):
        self.ensure_one()
        if not self.wallet_id:
            return self.env["account.analytic.line"]
        return self.env["account.analytic.line"].search(
            self._build_candidate_domain(),
            order="date asc, id asc",
        )

    # ==================================================================
    # ACCIONES
    # ==================================================================
    def action_load_candidates(self):
        """Recarga la selección con los candidatos que cumplen los filtros.

        Reabre el mismo wizard (mismo ``res_id``) para que el usuario siga
        iterando sobre filtros sin perder el contexto.
        """
        self.ensure_one()
        self.line_ids = [(6, 0, self._search_candidates().ids)]
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": dict(self.env.context),
        }

    def action_assign(self):
        """Vincula los timesheets seleccionados a la bolsa destino."""
        self.ensure_one()
        if not self.wallet_id._is_consumable():
            raise UserError(
                _(
                    "La bolsa '%s' no admite nuevos consumos en su estado actual."
                )
                % self.wallet_id.display_name
            )
        if not self.line_ids:
            raise UserError(_("Seleccione al menos un timesheet para asignar."))
        already_assigned = self.line_ids.filtered("hour_wallet_id")
        if already_assigned:
            raise UserError(
                _(
                    "Los siguientes timesheets ya están vinculados a una bolsa "
                    "y no pueden reasignarse:\n%s"
                )
                % "\n".join(
                    "- %s (%s)"
                    % (line.display_name or line.name or line.id,
                       line.hour_wallet_id.display_name)
                    for line in already_assigned
                )
            )
        # Validación previa de capacidad: evita asignar y luego romper límite.
        self.wallet_id._check_consumption_allowed(self.total_selected_hours)
        self.line_ids.write({"hour_wallet_id": self.wallet_id.id})
        self.wallet_id.message_post(
            body=_(
                "Se vincularon %(n)d timesheets a la bolsa (%(h).2f h)."
            )
            % {"n": len(self.line_ids), "h": self.total_selected_hours},
        )
        return {"type": "ir.actions.act_window_close"}
