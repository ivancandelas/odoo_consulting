# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    hour_wallet_ids = fields.One2many(
        "hour.wallet", "partner_id", string="Bolsas de horas"
    )
    hour_wallet_count = fields.Integer(
        compute="_compute_hour_wallet_count", string="# Bolsas"
    )
    hour_wallet_active_hours = fields.Float(
        compute="_compute_hour_wallet_count",
        string="Horas activas disponibles",
        digits=(12, 2),
    )

    @api.depends("hour_wallet_ids.state", "hour_wallet_ids.hours_available")
    def _compute_hour_wallet_count(self):
        for partner in self:
            partner.hour_wallet_count = len(partner.hour_wallet_ids)
            partner.hour_wallet_active_hours = sum(
                w.hours_available for w in partner.hour_wallet_ids if w.state == "active"
            )

    def action_view_hour_wallets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Bolsas de horas"),
            "res_model": "hour.wallet",
            "view_mode": "list,kanban,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
