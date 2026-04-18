# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    default_hour_wallet_id = fields.Many2one(
        "hour.wallet",
        string="Bolsa por defecto",
        domain="""[
            ('state', '=', 'active'),
            '|', ('partner_id', '=', partner_id), ('partner_id', '=', False),
        ]""",
        help="Bolsa sugerida automáticamente al imputar horas en este proyecto.",
    )
    hour_wallet_ids = fields.One2many(
        "hour.wallet", "project_id", string="Bolsas del proyecto"
    )
    hour_wallet_count = fields.Integer(
        compute="_compute_hour_wallet_count", string="# Bolsas"
    )

    @api.depends("hour_wallet_ids")
    def _compute_hour_wallet_count(self):
        for project in self:
            project.hour_wallet_count = len(project.hour_wallet_ids)

    def action_view_hour_wallets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Bolsas de horas"),
            "res_model": "hour.wallet",
            "view_mode": "list,kanban,form",
            "domain": [("project_id", "=", self.id)],
            "context": {
                "default_project_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }
