{
    "name": "Actas de Reunión - Integración con Proyectos",
    "summary": "Vincula actas de reunión con proyectos y genera tareas desde compromisos.",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "Ivan Candelas",
    "website": "https://nxscore.mx",
    "category": "Productivity/Meetings",
    "depends": ["meeting_minutes_base", "project"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/meeting_minute_to_task_wizard_views.xml",
        "views/meeting_minute_views.xml",
        "views/meeting_minute_commitment_views.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
