# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    hour_wallet_id = fields.Many2one(
        "hour.wallet",
        string="Bolsa de horas sugerida",
        domain="""[
            ('state', '=', 'active'),
            '|', ('partner_id', '=', partner_id), ('partner_id', '=', False),
            '|', ('project_id', '=', project_id), ('project_id', '=', False),
        ]""",
        help="Si se define, se usa como bolsa por defecto al registrar horas "
             "sobre esta tarea (prioridad sobre la bolsa por defecto del proyecto).",
    )

    @api.onchange("project_id")
    def _onchange_project_hour_wallet(self):
        for task in self:
            if task.project_id and task.project_id.default_hour_wallet_id and not task.hour_wallet_id:
                task.hour_wallet_id = task.project_id.default_hour_wallet_id
