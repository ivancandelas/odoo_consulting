[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Actas de Reunión — Base
=======================

Documentación estructurada de reuniones con clientes o equipos
internos: asistentes, agenda, desarrollo, conclusiones, compromisos y
trazabilidad entre reuniones relacionadas.

Es el núcleo de la suite de actas. Los módulos complementarios añaden
integraciones opcionales con proyectos, calendario, reportes y correo.

**Tabla de contenido**

* [Descripción](#descripción)
* [Uso](#uso)
  * [Crear un acta](#crear-un-acta)
  * [Ciclo de vida de la reunión](#ciclo-de-vida-de-la-reunión)
  * [Asistentes](#asistentes)
  * [Compromisos](#compromisos)
  * [Reuniones de seguimiento](#reuniones-de-seguimiento)
* [Créditos](#créditos)

Descripción
===========

Un acta representa una reunión: su planeación, su ejecución y sus
resultados. El módulo organiza la información en bloques claros:

* **Datos generales**: título, cliente, fecha, lugar, objetivo.
* **Agenda**: puntos a tratar antes de la reunión.
* **Desarrollo / notas**: narrativa de lo ocurrido durante la sesión.
* **Conclusiones**: acuerdos finales y resultados.
* **Compromisos**: acciones con responsable y fecha límite derivadas
  de la reunión.

Cada acta tiene un folio único generado automáticamente y una
cronología (chatter) donde quedan registrados todos los cambios
relevantes.

Uso
===

Crear un acta
-------------

Desde el menú **Actas de Reunión → Actas → Nuevo**, capturar:

* Título de la reunión
* Cliente (opcional)
* Responsable
* Fecha y hora programada
* Duración estimada
* Lugar
* Objetivo
* Agenda del día

Al guardar, el sistema asigna automáticamente un folio
(`ACTA/AAAA/NNNNN`).

Ciclo de vida de la reunión
---------------------------

Las actas siguen los siguientes estados:

1. **Borrador** — en preparación.
2. **Programada** — confirmada para realizarse.
3. **En curso** — la reunión ya inició; el sistema registra la hora
   real de inicio.
4. **Finalizada** — concluida; se registra la hora real de fin y la
   duración real.
5. **Cancelada** — la reunión no se llevará a cabo.

Los botones de acción (**Programar**, **Iniciar**, **Finalizar**,
**Cancelar**) reflejan el estado actual. Las actas finalizadas pueden
reabrirse a borrador si hay correcciones importantes que hacer.

Asistentes
----------

Cada acta mantiene una lista de asistentes convocados. Por cada uno
se indica:

* Persona convocada
* Empresa a la que pertenece
* Tipo de asistencia: presencial, remoto o delegado
* Si delegó, quién asistió en su nombre
* Si efectivamente asistió
* Observaciones

Compromisos
-----------

Los compromisos capturan acciones acordadas en la reunión:

* Descripción
* Responsable
* Fecha límite
* Estado: pendiente, en curso, hecho, cancelado

Se gestionan desde la misma acta y sirven como base para el
seguimiento en reuniones posteriores.

Reuniones de seguimiento
------------------------

Desde cualquier acta se puede generar una **reunión derivada** para
dar continuidad al tema. El asistente de seguimiento permite
clasificar el tipo (técnica, comercial, validación, seguimiento
interno, otro) y opcionalmente copiar los compromisos pendientes a la
nueva reunión.

Las reuniones quedan enlazadas formando un hilo: se puede navegar
desde una reunión a su origen, sus derivadas y todo el hilo completo.

Créditos
========

Autores
-------

* Ivan Candelas

Mantenedor
----------

Ivan Candelas — <https://nxscore.mx>
