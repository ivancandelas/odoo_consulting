{
    "name": "Actas de Reunión - Envío por Correo",
    "summary": "Envía el acta de reunión al cliente por email con el PDF adjunto.",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "Ivan Candelas",
    "website": "https://nxscore.mx",
    "category": "Productivity/Meetings",
    "depends": ["meeting_minutes_report", "mail"],
    "data": [
        "data/mail_template_data.xml",
        "views/meeting_minute_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
