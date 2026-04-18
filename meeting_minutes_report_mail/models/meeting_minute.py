from odoo import _, fields, models
from odoo.exceptions import UserError


class MeetingMinute(models.Model):
    _inherit = "meeting.minute"

    sent_by_email = fields.Boolean(
        string="Enviada por correo", readonly=True, copy=False, tracking=True,
    )
    last_sent_date = fields.Datetime(
        string="Última fecha de envío", readonly=True, copy=False,
    )

    def _get_default_mail_recipients(self):
        self.ensure_one()
        partners = self.env["res.partner"]
        if self.partner_id:
            partners |= self.partner_id
        partners |= self.attendee_ids.filtered("attended").mapped("partner_id")
        return partners

    def action_send_by_email(self):
        self.ensure_one()
        if not self.partner_id and not self.attendee_ids:
            raise UserError(_(
                "Debe asignar un cliente o al menos un asistente con correo antes de enviar el acta."
            ))
        template = self.env.ref(
            "meeting_minutes_report_mail.email_template_meeting_minute",
            raise_if_not_found=False,
        )
        default_partner_ids = self._get_default_mail_recipients().ids
        ctx = {
            "default_model": "meeting.minute",
            "default_res_ids": self.ids,
            "default_use_template": bool(template),
            "default_template_id": template.id if template else False,
            "default_composition_mode": "comment",
            "default_partner_ids": default_partner_ids,
            "default_email_layout_xmlid": "mail.mail_notification_layout_with_responsible_signature",
            "mark_meeting_minute_as_sent": True,
            "force_email": True,
        }
        return {
            "type": "ir.actions.act_window",
            "name": _("Enviar acta por correo"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": ctx,
        }

    def _message_post_after_hook(self, message, msg_vals):
        if self.env.context.get("mark_meeting_minute_as_sent") and msg_vals.get("partner_ids"):
            self.sudo().write({
                "sent_by_email": True,
                "last_sent_date": fields.Datetime.now(),
            })
        return super()._message_post_after_hook(message, msg_vals)
