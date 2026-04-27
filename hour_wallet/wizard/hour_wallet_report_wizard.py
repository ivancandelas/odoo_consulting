# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HourWalletReportWizard(models.TransientModel):
    """Asistente para generar el reporte periódico de consumo de bolsas."""

    _name = "hour.wallet.report.wizard"
    _description = "Asistente reporte de consumo de bolsas"

    partner_id = fields.Many2one("res.partner", string="Cliente")
    wallet_ids = fields.Many2many(
        "hour.wallet",
        string="Bolsas",
        domain="[('partner_id', '=', partner_id)] if partner_id else []",
    )
    date_from = fields.Date(
        string="Desde",
        required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=7),
    )
    date_to = fields.Date(
        string="Hasta",
        required=True,
        default=fields.Date.context_today,
    )
    group_by = fields.Selection(
        [("wallet", "Por bolsa"), ("user", "Por usuario"), ("task", "Por tarea")],
        default="wallet",
        required=True,
    )
    include_exhausted = fields.Boolean(
        string="Incluir bolsas agotadas/vencidas",
        default=True,
    )

    @api.onchange("partner_id")
    def _onchange_partner_clear_wallets(self):
        for wiz in self:
            if wiz.wallet_ids and wiz.partner_id:
                wiz.wallet_ids = wiz.wallet_ids.filtered(
                    lambda w: w.partner_id == wiz.partner_id
                )

    def _get_wallets(self):
        self.ensure_one()
        if self.wallet_ids:
            return self.wallet_ids
        domain = []
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        if not self.include_exhausted:
            domain.append(("state", "in", ("active",)))
        return self.env["hour.wallet"].search(domain)

    def _get_report_data(self):
        """Prepara los datos que alimentan el QWeb."""
        self.ensure_one()
        if self.date_to < self.date_from:
            raise UserError(_("La fecha final no puede ser anterior a la inicial."))
        wallets = self._get_wallets()
        if not wallets:
            raise UserError(_("No hay bolsas que coincidan con los criterios."))
        Line = self.env["account.analytic.line"]
        data = []
        for wallet in wallets:
            lines = Line.search(
                [
                    ("hour_wallet_id", "=", wallet.id),
                    ("date", ">=", self.date_from),
                    ("date", "<=", self.date_to),
                ],
                order="date asc",
            )
            billable_lines = lines.filtered("is_billable")
            non_billable_lines = lines - billable_lines
            data.append(
                {
                    "wallet": wallet,
                    "lines": lines,
                    "period_hours": sum(lines.mapped("unit_amount")),
                    "period_hours_billable": sum(
                        billable_lines.mapped("unit_amount")
                    ),
                    "period_hours_non_billable": sum(
                        non_billable_lines.mapped("unit_amount")
                    ),
                }
            )
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "group_by": self.group_by,
            "partner": self.partner_id,
            "wallets_data": data,
            "generated_on": fields.Date.context_today(self),
            "generated_by": self.env.user,
        }

    def action_preview(self):
        """Genera y muestra el PDF sin enviarlo.

        No se pasa `data=` para evitar que Odoo serialice los recordsets.
        El abstract model `report.hour_wallet.report_hour_wallet_consumption`
        reconstruye los datos a partir del wizard.
        """
        self.ensure_one()
        self._get_report_data()  # valida antes de generar
        return self.env.ref(
            "hour_wallet.action_report_hour_wallet_consumption"
        ).report_action(self)

    def action_send_by_email(self):
        """Abre el compositor de correo con la plantilla precargada.

        Sigue el patrón de `sale.order.action_quotation_send`: el usuario
        revisa destinatarios, asunto y cuerpo antes de enviar. El PDF del
        reporte se adjunta automáticamente vía `report_template_ids` de la
        plantilla.
        """
        self.ensure_one()
        self._get_report_data()  # valida antes de abrir el compositor
        if not self.partner_id:
            raise UserError(
                _("Seleccione un cliente para enviar el reporte por correo.")
            )
        template = self.env.ref(
            "hour_wallet.mail_template_hour_wallet_report",
            raise_if_not_found=False,
        )
        ctx = {
            "default_model": "hour.wallet.report.wizard",
            "default_res_ids": self.ids,
            "default_composition_mode": "comment",
            "default_use_template": bool(template),
            "default_template_id": template.id if template else False,
            "default_partner_ids": [self.partner_id.id],
            "force_email": True,
        }
        return {
            "type": "ir.actions.act_window",
            "name": _("Enviar reporte por correo"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": ctx,
        }
