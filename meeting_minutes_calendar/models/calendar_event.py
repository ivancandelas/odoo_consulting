from odoo import _, fields, models

SYNC_CONTEXT_KEY = "skip_meeting_minute_sync"

EVENT_TO_MINUTE_FIELDS = (
    "start", "stop", "location",
    "name", "description", "user_id", "partner_ids",
)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    meeting_minute_id = fields.Many2one(
        "meeting.minute", string="Acta de reunión",
        ondelete="set null", index=True, copy=False,
    )

    def _prepare_meeting_minute_vals(self):
        """Vals para generar un acta prellenada desde el evento."""
        self.ensure_one()
        duration = 1.0
        if self.start and self.stop and self.stop > self.start:
            duration = round((self.stop - self.start).total_seconds() / 3600.0, 2)

        customer = self.partner_ids.filtered("is_company")[:1]
        if not customer and self.partner_ids:
            customer = self.partner_ids.mapped("parent_id").filtered("is_company")[:1]

        attendee_cmds = [
            (0, 0, {"partner_id": pid, "attendance_type": "onsite"})
            for pid in self.partner_ids.ids
        ]

        return {
            "title": self.name or _("Reunión"),
            "scheduled_date": self.start or fields.Datetime.now(),
            "duration": duration,
            "location": self.location or False,
            "agenda": self.description or False,
            "user_id": (self.user_id or self.env.user).id,
            "partner_id": customer.id if customer else False,
            "attendee_ids": attendee_cmds,
            "calendar_event_id": self.id,
        }

    def action_create_or_open_meeting_minute(self):
        """Idempotente: abre el acta vinculada; la crea prellenada si no existe."""
        self.ensure_one()
        Minute = self.env["meeting.minute"]
        minute = self.meeting_minute_id
        if not minute:
            minute = Minute.search(
                [("calendar_event_id", "=", self.id)], limit=1,
            )
        if not minute:
            minute = Minute.with_context(
                **{SYNC_CONTEXT_KEY: True}
            ).create(self._prepare_meeting_minute_vals())
        if self.meeting_minute_id != minute:
            # `dont_notify` evita el chequeo de organizador de google_calendar:
            # `meeting_minute_id` es un FK interno que no se sincroniza con Google,
            # así que un asistente que no es el organizador debe poder escribirlo.
            self.with_context(
                **{SYNC_CONTEXT_KEY: True}, dont_notify=True
            ).write({"meeting_minute_id": minute.id})
        return {
            "type": "ir.actions.act_window",
            "name": _("Acta de reunión"),
            "res_model": "meeting.minute",
            "res_id": minute.id,
            "view_mode": "form",
            "target": "current",
        }

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get(SYNC_CONTEXT_KEY):
            return res
        if not any(f in vals for f in EVENT_TO_MINUTE_FIELDS):
            return res
        for event in self:
            minute = event.meeting_minute_id
            if not minute or minute.state not in ("draft", "scheduled"):
                continue
            minute_vals = {}
            if "start" in vals and event.start and event.start != minute.scheduled_date:
                minute_vals["scheduled_date"] = event.start
            if ("start" in vals or "stop" in vals) and event.start and event.stop \
                    and event.stop > event.start:
                duration = (event.stop - event.start).total_seconds() / 3600.0
                duration = round(duration, 2)
                if duration != round(minute.duration or 0.0, 2):
                    minute_vals["duration"] = duration
            if "location" in vals and (event.location or "") != (minute.location or ""):
                minute_vals["location"] = event.location or False
            if "name" in vals and event.name and event.name != minute.title:
                minute_vals["title"] = event.name
            if "description" in vals and (event.description or "") != (minute.agenda or ""):
                minute_vals["agenda"] = event.description or False
            if "user_id" in vals and event.user_id and event.user_id != minute.user_id:
                minute_vals["user_id"] = event.user_id.id
            if "partner_ids" in vals:
                # Add-only: no borramos líneas existentes para preservar
                # attendance_type / attended / delegate_partner_id / note.
                existing = set(minute.attendee_ids.mapped("partner_id").ids)
                new_partner_ids = [
                    pid for pid in event.partner_ids.ids if pid not in existing
                ]
                if new_partner_ids:
                    minute_vals["attendee_ids"] = [
                        (0, 0, {"partner_id": pid, "attendance_type": "onsite"})
                        for pid in new_partner_ids
                    ]
            if minute_vals:
                minute.with_context(**{SYNC_CONTEXT_KEY: True}).write(minute_vals)
                minute.message_post(body=minute._sync_from_event_message(minute_vals))
        return res
