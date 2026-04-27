# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    is_billable = fields.Boolean(
        string="Facturable",
        default=True,
        index=True,
        help="Si está marcada, la hora se reporta al cliente como facturable. "
             "Las horas no facturables siguen consumiendo la bolsa pero se "
             "muestran por separado en el reporte enviado al cliente.",
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
    def _check_wallet_reassignment_allowed(self, new_wallet_id):
        """Impide reasignar un timesheet a otra bolsa.

        Una vez vinculado a una bolsa, el consumo queda "congelado":
        - Mover a otra bolsa queda bloqueado para cualquier usuario (evita
          doble conteo y pérdida de trazabilidad del consumo reconocido).
        - Desvincular (poner a False) queda permitido solo para el grupo
          manager, como escape hatch ante errores de asignación.

        El contexto ``hour_wallet_force_reassign=True`` permite saltar la
        restricción; reservado para flujos internos (cron, migraciones).
        """
        if self.env.context.get("hour_wallet_force_reassign"):
            return
        is_manager = self.env.user.has_group(
            "hour_wallet.group_hour_wallet_manager"
        )
        for line in self:
            if not line.hour_wallet_id:
                continue
            if new_wallet_id and new_wallet_id != line.hour_wallet_id.id:
                raise UserError(
                    _(
                        "El timesheet '%(line)s' ya está vinculado a la bolsa "
                        "'%(wallet)s'. No es posible reasignarlo a otra bolsa."
                    )
                    % {
                        "line": line.display_name or line.name or line.id,
                        "wallet": line.hour_wallet_id.display_name,
                    }
                )
            if not new_wallet_id and not is_manager:
                raise UserError(
                    _(
                        "Solo un responsable de bolsas puede desvincular un "
                        "timesheet de la bolsa '%s'."
                    )
                    % line.hour_wallet_id.display_name
                )

    def action_unlink_from_wallet(self):
        """Desvincula la línea de su bolsa sin borrar el timesheet.

        La línea conserva su proyecto/tarea y queda disponible para
        asignarse de nuevo (a la misma bolsa u otra). El lock de
        ``_check_wallet_reassignment_allowed`` ya restringe esta acción
        al grupo manager.
        """
        lines_to_clear = self.filtered("hour_wallet_id")
        if lines_to_clear:
            lines_to_clear.write({"hour_wallet_id": False})
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_block_if_wallet_linked(self):
        """Impide borrar un timesheet ligado a una bolsa de horas.

        Protege el consumo ya reconocido: si el usuario quiere eliminar
        la línea, primero debe desvincularla de la bolsa (acción reservada
        al grupo manager). Así evitamos pérdidas silenciosas del consumo
        registrado.

        El contexto ``hour_wallet_force_reassign=True`` bypassa la regla
        para flujos internos (migraciones, cron).
        """
        if self.env.context.get("hour_wallet_force_reassign"):
            return
        linked = self.filtered("hour_wallet_id")
        if not linked:
            return
        wallets = ", ".join(
            sorted({line.hour_wallet_id.display_name for line in linked})
        )
        raise UserError(
            _(
                "No se puede eliminar un timesheet vinculado a una bolsa de "
                "horas (%s).\n"
                "Desvincúlelo primero desde el form de la bolsa "
                "(acción 'Desvincular') y luego elimínelo."
            )
            % wallets
        )

    def action_delete_from_wallet(self):
        """Elimina completamente la línea.

        Solo aplica a timesheets **sin tarea asignada** (consumos directos
        contra la bolsa). Si la línea tiene ``task_id``, se impide el
        borrado: hay que usar ``action_unlink_from_wallet`` para
        preservar el registro ligado a la tarea.

        El contexto ``hour_wallet_force_reassign`` bypassa el ondelete
        guard (``_unlink_block_if_wallet_linked``) porque esta acción
        es justamente el flujo explícito y auditado de eliminación;
        está ya restringida al grupo manager en la vista.
        """
        with_task = self.filtered("task_id")
        if with_task:
            raise UserError(
                _(
                    "No se puede eliminar un timesheet ligado a una tarea. "
                    "Use 'Desvincular' para mantenerlo en la tarea y liberar "
                    "las horas de la bolsa."
                )
            )
        self.with_context(hour_wallet_force_reassign=True).unlink()
        return True

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
            wallet.invalidate_recordset([
                "hours_consumed",
                "hours_consumed_billable",
                "hours_consumed_non_billable",
                "hours_available",
            ])
        for wallet, delta in deltas.items():
            wallet._check_consumption_allowed(0.0)  # re-valida estado tras update
        return lines

    def write(self, vals):
        if "hour_wallet_id" in vals:
            self._check_wallet_reassignment_allowed(vals["hour_wallet_id"])
        tracked = ("hour_wallet_id", "unit_amount", "is_billable")
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
            touched.invalidate_recordset([
                "hours_consumed",
                "hours_consumed_billable",
                "hours_consumed_non_billable",
                "hours_available",
            ])
            # Valida cada bolsa tocada (detecta agotamiento / vencimiento).
            for wallet in touched:
                wallet._check_consumption_allowed(0.0)
        return res
