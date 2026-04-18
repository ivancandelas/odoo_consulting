# -*- coding: utf-8 -*-
from . import models
from . import wizard
from . import report


def _post_init_hook(env):
    """Vincula el reporte a la plantilla de correo al terminar la instalación.

    Evita depender del orden de carga de data-files (el reporte y la plantilla
    se cargan en momentos distintos, y un `ref()` en XML podría ejecutarse
    antes de que el reporte exista).
    """
    template = env.ref(
        "hour_wallet.mail_template_hour_wallet_report",
        raise_if_not_found=False,
    )
    report = env.ref(
        "hour_wallet.action_report_hour_wallet_consumption",
        raise_if_not_found=False,
    )
    if template and report and report not in template.report_template_ids:
        template.report_template_ids = [(4, report.id)]
