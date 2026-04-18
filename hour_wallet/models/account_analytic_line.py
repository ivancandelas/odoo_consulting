# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    """Extiende la línea analítica (timesheet) para enlazarla a una bolsa.

    La asignación sigue este orden de preferencia:
      1. Manual (usuario selecciona la bolsa explícitamente).
      2. Automática por proyecto (si el proyecto tiene bolsa por defecto).
      3. Sugerida: única bolsa activa para el partner del proyecto.
    """

    _inherit = "account.analytic.line"

    hour_wallet_id = fields.Many2one(
        "hour.wallet",
        string="Bolsa de horas",
        index=True,
        ondelete="restrict",
        domain="""[
            ('state', '=', 'active'),
            '|', ('partner_id', '=', wallet_partner_id), ('partner_id', '=', False),
            '|', ('project_id', '=', project_id), ('project_id', '=', False),
        ]""",
    )
    wallet_partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_wallet_partner_id",
        store=False,
        help="Partner efectivo para filtrar bolsas; viene del proyecto o tarea.",
    )
    wallet_available_hours = fields.Float(
        related="hour_wallet_id.hours_available",
        string="Horas disponibles bolsa",
        readonly=True,
    )
    wallet_state = fields.Selection(
        related="hour_wallet_id.state",
        readonly=True,
        string="Estado bolsa",
    )

    # ------------------------------------------------------------------
    # COMPUTES / ONCHANGES
    # ------------------------------------------------------------------
    @api.depends("project_id", "task_id")
    def _compute_wallet_partner_id(self):
        for line in self:
            partner = False
            if line.project_id and line.project_id.partner_id:
                partner = line.project_id.partner_id
            elif line.task_id and line.task_id.partner_id:
                partner = line.task_id.partner_id
            line.wallet_partner_id = partner

    @api.onchange("project_id", "task_id")
    def _onchange_project_assign_wallet(self):
        """Sugiere la bolsa a consumir al cambiar proyecto o tarea."""
        for line in self:
            if line.hour_wallet_id:
                continue
            wallet = line._default_wallet_for_line()
            if wallet:
                line.hour_wallet_id = wallet

    def _default_wallet_for_line(self):
        """Aplica la heurística de asignación automática de bolsa."""
        self.ensure_one()
        Wallet = self.env["hour.wallet"].sudo()
        # 1) Bolsa sugerida de la tarea
        if self.task_id and self.task_id.hour_wallet_id:
            candidate = self.task_id.hour_wallet_id
            if candidate.state == "active":
                return candidate
        # 2) Bolsa por defecto del proyecto
        if self.project_id and self.project_id.default_hour_wallet_id:
            candidate = self.project_id.default_hour_wallet_id
            if candidate.state == "active":
                return candidate
        # 3) Única bolsa activa del partner
        partner = self.wallet_partner_id
        if partner:
            domain = [("partner_id", "=", partner.id), ("state", "=", "active")]
            # Si hay proyecto, priorizar bolsas del mismo proyecto
            if self.project_id:
                by_project = Wallet.search(
                    domain + [("project_id", "=", self.project_id.id)], limit=2
                )
                if len(by_project) == 1:
                    return by_project
            candidates = Wallet.search(domain, limit=2)
            if len(candidates) == 1:
                return candidates
        return Wallet.browse()

    # ------------------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------------------
    def _validate_wallet_consumption(self, delta_by_wallet):
        """Valida el consumo por bolsa.

        :param delta_by_wallet: dict {wallet: horas_delta_a_aplicar}
        """
        for wallet, delta in delta_by_wallet.items():
            if not wallet:
                continue
            if delta <= 0:
                continue
            wallet._check_consumption_allowed(delta)

    # ------------------------------------------------------------------
    # CREATE / WRITE / UNLINK
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        deltas = {}
        for line in lines:
            if line.hour_wallet_id and line.unit_amount:
                deltas.setdefault(line.hour_wallet_id, 0.0)
                deltas[line.hour_wallet_id] += line.unit_amount
        # Excluir el propio consumo ya registrado al validar: check_consumption_allowed
        # usa hours_consumed (stored). Como acabamos de crear, ya está dentro; validamos
        # que el total no haya roto límites.
        for wallet in deltas:
            wallet.invalidate_recordset(["hours_consumed", "hours_available"])
        for wallet, delta in deltas.items():
            wallet._check_consumption_allowed(0.0)  # re-valida estado tras update
        return lines

    def write(self, vals):
        tracked = ("hour_wallet_id", "unit_amount")
        before = {}
        if any(k in vals for k in tracked):
            for line in self:
                before[line.id] = (line.hour_wallet_id, line.unit_amount)
        res = super().write(vals)
        if before:
            touched = self.env["hour.wallet"]
            for line in self:
                old_wallet, old_amount = before.get(line.id, (False, 0.0))
                if old_wallet:
                    touched |= old_wallet
                if line.hour_wallet_id:
                    touched |= line.hour_wallet_id
            touched.invalidate_recordset(["hours_consumed", "hours_available"])
            # Valida cada bolsa tocada (detecta agotamiento / vencimiento).
            for wallet in touched:
                wallet._check_consumption_allowed(0.0)
        return res
