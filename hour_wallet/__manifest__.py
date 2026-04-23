# -*- coding: utf-8 -*-
{
    "name": "Hour Wallet - Bolsas de Horas",
    "version": "18.0.1.0.2",
    "summary": "Gestión de bolsas de horas vendidas a clientes con control de saldo, vigencia y reportes.",
    "description": """
Hour Wallet
===========
Gestiona contratos o bolsas de horas por cliente:

* Modelo propio `hour.wallet` con ciclo de vida y saldo calculado.
* Extensión de timesheets (account.analytic.line) para registrar consumo.
* Validación de vigencia, saldo y reglas de uso.
* Reporte QWeb periódico orientado al cliente.
* Alertas de saldo bajo, vencimiento y agotamiento vía cron.
* Base preparada para portal del cliente y futura integración con ventas.
""",
    "author": "Ivan Candelas",
    "website": "https://nxscore.mx",
    "category": "Services/Timesheets",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "portal",
        "project",
        "hr_timesheet",
    ],
    "data": [
        "security/hour_wallet_security.xml",
        "security/ir.model.access.csv",
        "data/hour_wallet_sequence.xml",
        "data/hour_wallet_type_data.xml",
        "report/hour_wallet_report.xml",
        "report/hour_wallet_report_templates.xml",
        "data/mail_template_data.xml",
        "data/hour_wallet_cron.xml",
        "views/hour_wallet_type_views.xml",
        "views/hour_wallet_views.xml",
        "views/account_analytic_line_views.xml",
        "views/project_views.xml",
        "views/res_partner_views.xml",
        "wizard/hour_wallet_report_wizard_views.xml",
        "wizard/hour_wallet_assign_timesheets_wizard_views.xml",
        "views/hour_wallet_menus.xml",
    ],
    "demo": [
        "demo/hour_wallet_demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "_post_init_hook",
}
