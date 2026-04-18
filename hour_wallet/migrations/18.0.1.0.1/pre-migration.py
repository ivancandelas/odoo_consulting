# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Reabre la plantilla de correo a actualizaciones.

    La plantilla `mail_template_hour_wallet_report` se instaló originalmente
    dentro de un bloque `<data noupdate="1">`, por lo que Odoo ignora los
    cambios posteriores en su XML (modelo, asunto, cuerpo, etc.).

    Al bajar el flag noupdate antes de cargar los datos, el XML vigente
    reemplaza íntegramente el registro durante esta actualización.
    """
    cr.execute(
        """
        UPDATE ir_model_data
           SET noupdate = FALSE
         WHERE module = 'hour_wallet'
           AND name   = 'mail_template_hour_wallet_report'
        """
    )
