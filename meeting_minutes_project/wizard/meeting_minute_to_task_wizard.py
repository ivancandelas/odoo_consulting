from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MeetingMinuteToTaskWizard(models.TransientModel):
    _name = "meeting.minute.to.task.wizard"
    _description = "Asistente: Compromisos → Tareas"

    meeting_id = fields.Many2one(
        "meeting.minute", string="Acta", required=True, readonly=True,
    )
    project_id = fields.Many2one(
        "project.project", string="Proyecto destino", required=True,
    )
    commitment_ids = fields.Many2many(
        "meeting.minute.commitment", string="Compromisos a convertir",
        domain="[('meeting_id','=',meeting_id),('task_id','=',False),"
               "('state','not in',('done','cancelled'))]",
    )

    @api.onchange("meeting_id")
    def _onchange_meeting_id(self):
        if self.meeting_id and self.meeting_id.project_id and not self.project_id:
            self.project_id = self.meeting_id.project_id

    def action_create_tasks(self):
        self.ensure_one()
        if not self.commitment_ids:
            raise UserError(_("Seleccione al menos un compromiso para convertir."))
        tasks = self.env["project.task"]
        for commitment in self.commitment_ids:
            tasks |= commitment._create_task(project=self.project_id)
        self.meeting_id.message_post(body=_(
            "Se crearon %d tarea(s) en el proyecto %s."
        ) % (len(tasks), self.project_id.display_name))
        return {
            "type": "ir.actions.act_window",
            "name": _("Tareas generadas"),
            "res_model": "project.task",
            "view_mode": "list,form",
            "domain": [("id", "in", tasks.ids)],
            "target": "current",
        }
