from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MeetingMinute(models.Model):
    _inherit = "meeting.minute"

    project_id = fields.Many2one(
        "project.project", string="Proyecto",
        tracking=True, ondelete="set null",
    )
    task_ids = fields.One2many(
        "project.task", "meeting_minute_id", string="Tareas generadas",
    )
    task_count = fields.Integer(
        string="# Tareas", compute="_compute_task_count",
    )

    @api.depends("task_ids")
    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)

    @api.onchange("project_id")
    def _onchange_project_id(self):
        if self.project_id and self.project_id.partner_id and not self.partner_id:
            self.partner_id = self.project_id.partner_id

    def action_open_task_wizard(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(_(
                "Debe asignar un proyecto al acta antes de convertir compromisos en tareas."
            ))
        commitments = self.commitment_ids.filtered(
            lambda c: not c.task_id and c.state not in ("done", "cancelled")
        )
        if not commitments:
            raise UserError(_(
                "No hay compromisos pendientes disponibles para convertir en tareas."
            ))
        return {
            "type": "ir.actions.act_window",
            "name": _("Convertir compromisos en tareas"),
            "res_model": "meeting.minute.to.task.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_meeting_id": self.id,
                "default_project_id": self.project_id.id,
                "default_commitment_ids": [(6, 0, commitments.ids)],
            },
        }

    def action_view_tasks(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("project.action_view_task")
        action.update({
            "domain": [("id", "in", self.task_ids.ids)],
            "context": {
                "default_project_id": self.project_id.id if self.project_id else False,
                "default_meeting_minute_id": self.id,
            },
        })
        return action
