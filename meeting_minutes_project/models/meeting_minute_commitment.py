from markupsafe import Markup

from odoo import _, fields, models
from odoo.exceptions import UserError


class MeetingMinuteCommitment(models.Model):
    _inherit = "meeting.minute.commitment"

    project_id = fields.Many2one(
        "project.project", string="Proyecto",
        help="Proyecto donde se crearán las tareas derivadas del compromiso.",
    )
    task_id = fields.Many2one(
        "project.task", string="Tarea", readonly=True, copy=False,
        ondelete="set null",
    )

    def _resolve_task_user(self):
        """Resuelve el usuario Odoo a asignar a la tarea.

        Orden:
          1. `responsible_user_id` si está definido.
          2. Usuario interno único vinculado a `responsible_partner_id`.
          3. Ninguno — la tarea se crea sin asignar y se deja nota en chatter.
        """
        self.ensure_one()
        if self.responsible_user_id:
            return self.responsible_user_id
        if self.responsible_partner_id:
            user = self.env["res.users"].search([
                ("partner_id", "=", self.responsible_partner_id.id),
                ("share", "=", False),
                ("active", "=", True),
            ], limit=2)
            if len(user) == 1:
                return user
        return self.env["res.users"]

    def _prepare_task_vals(self, project):
        self.ensure_one()
        task_user = self._resolve_task_user()
        return {
            "name": (self.description or "").split("\n")[0][:200] or _("Compromiso"),
            "description": self.description,
            "project_id": project.id,
            "user_ids": [(6, 0, task_user.ids)] if task_user else [(6, 0, [])],
            "date_deadline": self.due_date,
            "partner_id": self.meeting_id.partner_id.id if self.meeting_id.partner_id else False,
            "meeting_minute_id": self.meeting_id.id,
            "meeting_minute_commitment_id": self.id,
        }

    def _create_task(self, project=None):
        self.ensure_one()
        if self.task_id:
            return self.task_id
        project = project or self.project_id or self.meeting_id.project_id
        if not project:
            raise UserError(_(
                "El compromiso '%s' no tiene proyecto asignado y el acta tampoco."
            ) % (self.description or ""))

        task = self.env["project.task"].create(self._prepare_task_vals(project))
        self.write({"task_id": task.id, "state": "in_progress", "project_id": project.id})

        task_user = self._resolve_task_user()
        if not task_user and self.responsible_partner_id:
            task.message_post(body=Markup(_(
                "Tarea creada sin asignado. El responsable del compromiso "
                "es <b>%s</b>, que no es un usuario interno de Odoo. "
                "Asigne manualmente al responsable operativo."
            )) % self.responsible_partner_id.display_name)
        return task

    def action_open_task(self):
        self.ensure_one()
        if not self.task_id:
            raise UserError(_("Este compromiso aún no tiene una tarea generada."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "res_id": self.task_id.id,
            "view_mode": "form",
            "target": "current",
        }
