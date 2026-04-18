[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Actas de Reunión — Integración con Calendario
=============================================

Vincula actas de reunión con eventos del calendario de Odoo. El
calendario es la fuente natural para agendar la reunión; el acta
documenta su ejecución y resultados.

**Tabla de contenido**

* [Descripción](#descripción)
* [Uso](#uso)
  * [Crear un acta desde un evento](#crear-un-acta-desde-un-evento)
  * [Sincronización de cambios](#sincronización-de-cambios)
  * [Crear el evento desde el acta](#crear-el-evento-desde-el-acta)
* [Créditos](#créditos)

Descripción
===========

En la operación diaria, las reuniones se agendan primero en el
calendario (invitaciones, disponibilidad, salas). Cuando llega el
momento de documentar la sesión, este módulo permite generar un acta
directamente desde el evento, con todos los datos ya precargados:
título, fecha, lugar, asistentes y descripción.

Después, mientras la reunión esté en preparación, los cambios hechos
en el evento (añadir asistentes, mover la fecha, cambiar el lugar) se
reflejan automáticamente en el acta asociada.

Uso
===

Crear un acta desde un evento
-----------------------------

En cualquier evento del calendario aparece el botón **Crear/Abrir
acta**. Al pulsarlo:

* Si el evento aún no tiene acta, se crea una nueva con todos los
  datos precargados desde el evento y se abre.
* Si ya existe un acta vinculada, se abre directamente.

Nunca se duplican actas: el botón es idempotente.

Datos que se precargan al crear el acta:

* Título (nombre del evento)
* Fecha y hora programada
* Duración (calculada desde inicio/fin del evento)
* Lugar
* Descripción del evento como agenda inicial
* Responsable
* Cliente (inferido del primer contacto de tipo empresa entre los
  invitados)
* Asistentes (todos los invitados del evento)

Sincronización de cambios
-------------------------

Mientras el acta esté en estado **Borrador** o **Programada**, los
cambios hechos en el evento se propagan al acta:

* Cambio de fecha / duración / lugar → actualiza los mismos campos.
* Cambio de título → actualiza el título del acta.
* Cambio de responsable → actualiza el responsable del acta.
* Invitados añadidos al evento → se agregan como nuevos asistentes
  del acta.

Para no destruir trabajo del usuario, los asistentes ya presentes en
el acta **no se eliminan** aunque se quiten del evento: esto protege
datos como delegados, tipo de asistencia o notas. Si hace falta
eliminar un asistente del acta, se hace manualmente.

Una vez que la reunión inicia (estado **En curso** o posteriores), el
acta se vuelve autoritativa y deja de recibir cambios del evento:
refleja la ejecución real, no la planeación.

Cada sincronización deja un registro en el chatter del acta
indicando qué campos se actualizaron.

Crear el evento desde el acta
-----------------------------

Por compatibilidad con el flujo inverso, desde el acta también existe
el botón **Crear/Actualizar evento**, que genera (o actualiza) un
evento en el calendario a partir del acta. Útil cuando la
documentación de la reunión arranca antes que el agendamiento
formal.

Créditos
========

Autores
-------

* Ivan Candelas

Mantenedor
----------

Ivan Candelas — <https://nxscore.mx>
