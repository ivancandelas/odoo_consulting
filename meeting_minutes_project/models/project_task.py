from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    meeting_minute_id = fields.Many2one(
        "meeting.minute", string="Acta de origen",
        ondelete="set null", index=True,
    )
    meeting_minute_commitment_id = fields.Many2one(
        "meeting.minute.commitment", string="Compromiso de origen",
        ondelete="set null", index=True,
    )
