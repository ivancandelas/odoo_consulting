# -*- coding: utf-8 -*-
from odoo import api, models


class ReportHourWalletConsumption(models.AbstractModel):
    """Builder de valores para el QWeb de consumo de bolsas.

    Odoo 18 toma el diccionario que retorna `_get_report_values` como contexto
    de renderizado; es el mecanismo canónico para exponer `data` al template.
    """

    _name = "report.hour_wallet.report_hour_wallet_consumption"
    _description = "Hour Wallet Consumption Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Reconstruye siempre `data` desde el wizard (docids).

        `data` pasado por `report_action(data=...)` se serializa y pierde los
        recordsets; por eso se ignora aquí y se reconstruye server-side.
        """
        wizards = self.env["hour.wallet.report.wizard"].browse(docids)
        values = wizards._get_report_data() if wizards else {}
        return {
            "doc_ids": docids,
            "doc_model": "hour.wallet.report.wizard",
            "docs": wizards,
            "data": values,
        }
