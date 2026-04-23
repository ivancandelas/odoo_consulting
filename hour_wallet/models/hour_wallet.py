# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round


class HourWallet(models.Model):
    """Bolsa de horas vendida a un cliente.

    Representa un crédito de tiempo contratado por un partner, consumido por
    líneas de timesheet (account.analytic.line) vinculadas a esta bolsa.
    """

    _name = "hour.wallet"
    _description = "Bolsa de Horas"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = "date_end, name desc"
    _rec_name = "display_name"

    # ------------------------------------------------------------------
    # Identificación
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("Nuevo"),
        tracking=True,
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)
    description = fields.Char(string="Descripción", tracking=True)
    note = fields.Html(string="Notas internas")
    color = fields.Integer()
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Datos comerciales
    # ------------------------------------------------------------------
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        tracking=True,
        index=True,
        domain="[('is_company', '=', True), ('parent_id', '=', False)]",
    )
    project_id = fields.Many2one(
        "project.project",
        string="Proyecto",
        tracking=True,
        domain="['|', ('partner_id', '=', partner_id), ('partner_id', '=', False)]",
        help="Proyecto asociado; si se define, se usa como sugerencia por defecto "
             "para los timesheets.",
    )
    type_id = fields.Many2one(
        "hour.wallet.type",
        string="Tipo de bolsa",
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsable interno",
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )
    unit_price = fields.Monetary(
        string="Precio por hora (ref.)",
        currency_field="currency_id",
        help="Valor comercial de referencia; no implica facturación.",
    )
    amount_total = fields.Monetary(
        string="Valor total",
        currency_field="currency_id",
        compute="_compute_amount_total",
        store=True,
    )

    # ------------------------------------------------------------------
    # Volúmenes de horas
    # ------------------------------------------------------------------
    hours_purchased = fields.Float(
        string="Horas contratadas",
        required=True,
        default=0.0,
        tracking=True,
        digits=(12, 2),
    )
    hours_consumed = fields.Float(
        string="Horas consumidas",
        compute="_compute_hours_consumed",
        store=True,
        digits=(12, 2),
    )
    hours_available = fields.Float(
        string="Horas disponibles",
        compute="_compute_hours_consumed",
        store=True,
        digits=(12, 2),
    )
    consumption_percent = fields.Float(
        string="% consumido",
        compute="_compute_hours_consumed",
        store=True,
        aggregator="avg",
    )
    low_balance = fields.Boolean(
        string="Saldo bajo",
        compute="_compute_hours_consumed",
        store=True,
    )

    # ------------------------------------------------------------------
    # Vigencia y estado
    # ------------------------------------------------------------------
    date_start = fields.Date(
        string="Fecha inicio",
        default=fields.Date.context_today,
        tracking=True,
    )
    date_end = fields.Date(string="Fecha vencimiento", tracking=True)
    days_to_expire = fields.Integer(
        string="Días para vencer",
        compute="_compute_days_to_expire",
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activa"),
            ("exhausted", "Agotada"),
            ("expired", "Vencida"),
            ("closed", "Cerrada"),
        ],
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Reglas de consumo y alertas
    # ------------------------------------------------------------------
    allow_overdraft = fields.Boolean(
        string="Permitir sobregiro",
        help="Si está activo, se permite consumir más horas de las contratadas "
             "(con advertencia). Úselo solo como excepción controlada.",
    )
    alerts_enabled = fields.Boolean(string="Alertas activas", default=True)
    alert_threshold_percent = fields.Float(
        string="Umbral alerta saldo bajo (%)",
        default=20.0,
        help="Porcentaje de horas restantes a partir del cual se emite alerta.",
    )
    alert_days_before_expiration = fields.Integer(
        string="Días alerta pre-vencimiento",
        default=7,
    )
    low_balance_alert_sent = fields.Boolean(copy=False)
    expiration_alert_sent = fields.Boolean(copy=False)
    exhausted_alert_sent = fields.Boolean(copy=False)

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------
    timesheet_ids = fields.One2many(
        "account.analytic.line",
        "hour_wallet_id",
        string="Consumos (timesheets)",
    )
    timesheet_count = fields.Integer(
        compute="_compute_timesheet_count",
        string="# Consumos",
    )

    # Gancho para futura integración comercial (sale_timesheet/sale_order).
    # No se declara dependencia para no acoplar la primera versión.

    # ==================================================================
    # COMPUTES
    # ==================================================================
    @api.depends("name", "partner_id")
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.name or ""]
            if rec.partner_id:
                parts.append(rec.partner_id.display_name)
            rec.display_name = " - ".join(p for p in parts if p)

    @api.depends(
        "timesheet_ids.unit_amount",
        "timesheet_ids.hour_wallet_id",
        "hours_purchased",
        "alert_threshold_percent",
    )
    def _compute_hours_consumed(self):
        """Recalcula consumo, saldo, %, y flag de saldo bajo.

        Se usa read_group para rendimiento en consultas por batch.
        """
        consumed_by_wallet = {}
        if self.ids:
            groups = self.env["account.analytic.line"].read_group(
                domain=[("hour_wallet_id", "in", self.ids)],
                fields=["unit_amount:sum"],
                groupby=["hour_wallet_id"],
            )
            consumed_by_wallet = {
                g["hour_wallet_id"][0]: g["unit_amount"] for g in groups
            }
        for rec in self:
            consumed = consumed_by_wallet.get(rec.id, 0.0)
            rec.hours_consumed = float_round(consumed, precision_digits=2)
            rec.hours_available = float_round(
                rec.hours_purchased - consumed, precision_digits=2
            )
            if rec.hours_purchased:
                rec.consumption_percent = min(
                    100.0, (consumed / rec.hours_purchased) * 100.0
                )
            else:
                rec.consumption_percent = 0.0
            remaining_pct = 100.0 - rec.consumption_percent
            rec.low_balance = bool(
                rec.alerts_enabled
                and rec.hours_purchased
                and remaining_pct <= rec.alert_threshold_percent
                and rec.hours_available > 0
            )

    @api.depends("timesheet_ids")
    def _compute_timesheet_count(self):
        data = {}
        if self.ids:
            groups = self.env["account.analytic.line"].read_group(
                [("hour_wallet_id", "in", self.ids)],
                ["hour_wallet_id"],
                ["hour_wallet_id"],
            )
            data = {g["hour_wallet_id"][0]: g["hour_wallet_id_count"] for g in groups}
        for rec in self:
            rec.timesheet_count = data.get(rec.id, 0)

    @api.depends("unit_price", "hours_purchased")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = (rec.unit_price or 0.0) * (rec.hours_purchased or 0.0)

    @api.depends("date_end")
    def _compute_days_to_expire(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.date_end:
                rec.days_to_expire = (rec.date_end - today).days
            else:
                rec.days_to_expire = 0

    # ==================================================================
    # CONSTRAINTS
    # ==================================================================
    @api.constrains("hours_purchased")
    def _check_hours_purchased(self):
        for rec in self:
            if rec.hours_purchased <= 0:
                raise ValidationError(
                    _("Las horas contratadas deben ser mayores que cero.")
                )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    _("La fecha de vencimiento no puede ser anterior a la fecha de inicio.")
                )

    @api.constrains("alert_threshold_percent")
    def _check_threshold(self):
        for rec in self:
            if not (0.0 <= rec.alert_threshold_percent <= 100.0):
                raise ValidationError(
                    _("El umbral de alerta debe estar entre 0 y 100.")
                )

    # ==================================================================
    # CREATE / WRITE
    # ==================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("Nuevo"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "hour.wallet"
                ) or _("Nuevo")
        return super().create(vals_list)

    # ==================================================================
    # LÓGICA DE NEGOCIO EXPUESTA
    # ==================================================================
    def _is_consumable(self):
        """Indica si la bolsa admite registrar nuevo consumo ahora mismo."""
        self.ensure_one()
        return self.state == "active"

    def _check_consumption_allowed(self, new_hours, line=None):
        """Valida que se pueda consumir `new_hours` adicionales.

        Lanza UserError si el consumo no es permitido.
        Esta API es usada por la extensión de account.analytic.line.
        """
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.state in ("closed",):
            raise UserError(
                _("La bolsa '%s' está cerrada y no admite más consumos.") % self.display_name
            )
        if self.state == "draft":
            raise UserError(
                _("La bolsa '%s' está en borrador. Actívela antes de registrar consumo.")
                % self.display_name
            )
        if self.state == "expired" or (self.date_end and self.date_end < today):
            raise UserError(
                _("La bolsa '%s' está vencida (fecha fin %s).")
                % (self.display_name, self.date_end)
            )
        # Saldo proyectado tras aplicar este cambio
        projected_consumed = self.hours_consumed + new_hours
        overflow = projected_consumed - self.hours_purchased
        if float_compare(overflow, 0.0, precision_digits=2) > 0 and not self.allow_overdraft:
            raise UserError(
                _(
                    "No hay saldo suficiente en la bolsa '%(name)s'.\n"
                    "Contratadas: %(p).2f h · Consumidas: %(c).2f h · "
                    "Disponibles: %(a).2f h · Intento consumir: %(n).2f h."
                )
                % {
                    "name": self.display_name,
                    "p": self.hours_purchased,
                    "c": self.hours_consumed,
                    "a": self.hours_available,
                    "n": new_hours,
                }
            )

    # ==================================================================
    # TRANSICIONES DE ESTADO
    # ==================================================================
    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Solo se pueden activar bolsas en borrador."))
            if not rec.hours_purchased:
                raise UserError(_("Debe indicar las horas contratadas."))
            rec.state = "active"
        return True

    def action_close(self):
        for rec in self:
            if rec.state == "closed":
                continue
            rec.state = "closed"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.timesheet_ids:
                raise UserError(
                    _("No es posible volver a borrador una bolsa con consumos registrados.")
                )
            rec.state = "draft"
        return True

    def action_reopen(self):
        for rec in self:
            if rec.state not in ("closed", "exhausted", "expired"):
                continue
            rec.state = "active"
            rec.low_balance_alert_sent = False
            rec.expiration_alert_sent = False
            rec.exhausted_alert_sent = False
        return True

    # ==================================================================
    # ACCIONES UI
    # ==================================================================
    def action_view_timesheets(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "hr_timesheet.timesheet_action_all"
        )
        action["domain"] = [("hour_wallet_id", "=", self.id)]
        action["context"] = {
            "default_hour_wallet_id": self.id,
            "default_partner_id": self.partner_id.id,
            "default_project_id": self.project_id.id,
        }
        return action

    def action_open_report_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Generar reporte de consumo"),
            "res_model": "hour.wallet.report.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_wallet_ids": [(6, 0, self.ids)],
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_open_assign_timesheets_wizard(self):
        self.ensure_one()
        if not self._is_consumable():
            raise UserError(
                _(
                    "La bolsa '%s' no admite nuevos consumos en su estado actual."
                )
                % self.display_name
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Asignar timesheets a bolsa"),
            "res_model": "hour.wallet.assign.timesheets.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_wallet_id": self.id},
        }

    # ==================================================================
    # CRON: ESTADOS Y ALERTAS
    # ==================================================================
    @api.model
    def _cron_update_states_and_alerts(self):
        """Transiciones automáticas + envío de alertas.

        - Vencidas: date_end < today y activa → expired
        - Agotadas: hours_available <= 0 y activa → exhausted
        - Alertas: saldo bajo / pre-vencimiento.
        """
        today = fields.Date.context_today(self)
        wallets = self.search([("state", "=", "active")])
        for wallet in wallets:
            # Vencimiento
            if wallet.date_end and wallet.date_end < today:
                wallet.state = "expired"
                wallet._notify_alert("expired")
                continue
            # Agotamiento (sin overdraft)
            if (
                float_compare(wallet.hours_available, 0.0, precision_digits=2) <= 0
                and not wallet.allow_overdraft
            ):
                wallet.state = "exhausted"
                wallet._notify_alert("exhausted")
                continue
            if not wallet.alerts_enabled:
                continue
            # Saldo bajo
            if wallet.low_balance and not wallet.low_balance_alert_sent:
                wallet._notify_alert("low_balance")
                wallet.low_balance_alert_sent = True
            # Pre-vencimiento
            if wallet.date_end and wallet.alert_days_before_expiration:
                days_left = (wallet.date_end - today).days
                if (
                    0 <= days_left <= wallet.alert_days_before_expiration
                    and not wallet.expiration_alert_sent
                ):
                    wallet._notify_alert("expiring")
                    wallet.expiration_alert_sent = True

    def _notify_alert(self, kind):
        """Publica un mensaje en el chatter y crea una actividad para el responsable."""
        self.ensure_one()
        mapping = {
            "low_balance": (
                _("Saldo bajo en la bolsa"),
                _("La bolsa %(n)s alcanzó saldo bajo: %(a).2f h disponibles de %(p).2f h.")
                % {"n": self.display_name, "a": self.hours_available, "p": self.hours_purchased},
            ),
            "expiring": (
                _("Bolsa por vencer"),
                _("La bolsa %(n)s vence el %(d)s (%(days)s días).")
                % {"n": self.display_name, "d": self.date_end, "days": self.days_to_expire},
            ),
            "expired": (
                _("Bolsa vencida"),
                _("La bolsa %(n)s se marcó como vencida.") % {"n": self.display_name},
            ),
            "exhausted": (
                _("Bolsa agotada"),
                _("La bolsa %(n)s se marcó como agotada.") % {"n": self.display_name},
            ),
        }
        subject, body = mapping.get(kind, (_("Alerta"), ""))
        self.message_post(body=body, subject=subject)
        if self.user_id:
            self.activity_schedule(
                "mail.mail_activity_data_warning",
                summary=subject,
                note=body,
                user_id=self.user_id.id,
            )

    # ==================================================================
    # PORTAL
    # ==================================================================
    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = "/my/hour_wallet/%s" % rec.id
