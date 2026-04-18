from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

SYNC_CONTEXT_KEY = "skip_meeting_minute_sync"

MINUTE_TO_EVENT_FIELDS = ("scheduled_date", "duration", "location", "title")


class MeetingMinute(models.Model):
    _inherit = "meeting.minute"

    calendar_event_id = fields.Many2one(
        "calendar.event", string="Evento de calendario",
        copy=False, ondelete="set null", readonly=True,
    )

    def _prepare_calendar_event_vals(self):
        self.ensure_one()
        start = self.scheduled_date
        duration_hours = self.duration or 1.0
        stop = start + timedelta(hours=duration_hours) if start else False
        partner_ids = self.attendee_ids.mapped("partner_id").ids
        if self.partner_id and self.partner_id.id not in partner_ids:
            partner_ids.append(self.partner_id.id)
        if self.user_id and self.user_id.partner_id.id not in partner_ids:
            partner_ids.append(self.user_id.partner_id.id)
        return {
            "name": self.title or self.name,
            "start": start,
            "stop": stop,
            "duration": duration_hours,
            "location": self.location or "",
            "description": self.objective or "",
            "user_id": self.user_id.id,
            "partner_ids": [(6, 0, partner_ids)],
            "meeting_minute_id": self.id,
        }

    def _prepare_calendar_event_update_vals(self):
        """Subset de vals para actualizaciones incrementales acta→evento."""
        self.ensure_one()
        start = self.scheduled_date
        duration_hours = self.duration or 1.0
        stop = start + timedelta(hours=duration_hours) if start else False
        return {
            "name": self.title or self.name,
            "start": start,
            "stop": stop,
            "duration": duration_hours,
            "location": self.location or "",
        }

    def _sync_from_event_message(self, vals):
        labels = {
            "scheduled_date": _("Fecha programada"),
            "duration": _("Duración"),
            "location": _("Lugar"),
            "title": _("Título"),
            "agenda": _("Agenda / descripción"),
            "user_id": _("Responsable"),
            "attendee_ids": _("Asistentes (nuevos)"),
        }
        parts = [labels[k] for k in vals if k in labels]
        return _("Sincronizado desde el evento de calendario: %s") % ", ".join(parts)

    def action_create_or_update_calendar_event(self):
        self.ensure_one()
        if not self.scheduled_date:
            raise UserError(_("Debe fijar una fecha programada antes de crear el evento."))
        vals = self._prepare_calendar_event_vals()
        event_env = self.env["calendar.event"].with_context(**{SYNC_CONTEXT_KEY: True})
        if self.calendar_event_id:
            self.calendar_event_id.with_context(**{SYNC_CONTEXT_KEY: True}).write(vals)
            message = _("Evento de calendario actualizado.")
        else:
            event = event_env.create(vals)
            self.calendar_event_id = event.id
            message = _("Evento de calendario creado.")
        self.message_post(body=message)
        return self.action_open_calendar_event()

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get(SYNC_CONTEXT_KEY):
            return res
        if not any(f in vals for f in MINUTE_TO_EVENT_FIELDS):
            return res
        for rec in self.filtered("calendar_event_id"):
            if rec.state in ("done", "cancelled"):
                continue
            event_vals = rec._prepare_calendar_event_update_vals()
            rec.calendar_event_id.with_context(**{SYNC_CONTEXT_KEY: True}).write(event_vals)
        return res

    def action_open_calendar_event(self):
        self.ensure_one()
        if not self.calendar_event_id:
            raise UserError(_("Esta acta aún no tiene evento de calendario."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Evento"),
            "res_model": "calendar.event",
            "res_id": self.calendar_event_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_start(self):
        res = super().action_start()
        for rec in self.filtered("calendar_event_id"):
            rec.calendar_event_id.message_post(
                body=_("La reunión asociada ha iniciado: %s") % rec.name
            )
        return res

    def action_finish(self):
        res = super().action_finish()
        for rec in self.filtered("calendar_event_id"):
            rec.calendar_event_id.message_post(
                body=_("La reunión asociada ha finalizado: %s") % rec.name
            )
        return res
