# -*- coding: utf-8 -*-
from odoo import fields, models


class HourWalletType(models.Model):
    _name = "hour.wallet.type"
    _description = "Tipo / Categoría de Bolsa de Horas"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(help="Código corto para identificar el tipo en reportes.")
    sequence = fields.Integer(default=10)
    description = fields.Text()
    active = fields.Boolean(default=True)
    color = fields.Integer()

    _sql_constraints = [
        ("hour_wallet_type_code_uniq", "unique(code)",
         "El código del tipo de bolsa debe ser único."),
    ]
