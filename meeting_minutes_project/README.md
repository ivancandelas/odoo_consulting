[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Actas de Reunión — Integración con Proyectos
============================================

Vincula las actas de reunión con proyectos y permite convertir los
compromisos capturados en tareas operables desde el módulo de
Proyectos.

**Tabla de contenido**

* [Descripción](#descripción)
* [Uso](#uso)
  * [Asociar un acta a un proyecto](#asociar-un-acta-a-un-proyecto)
  * [Convertir compromisos en tareas](#convertir-compromisos-en-tareas)
  * [Seguimiento desde la tarea](#seguimiento-desde-la-tarea)
* [Créditos](#créditos)

Descripción
===========

Los compromisos derivados de una reunión muchas veces terminan siendo
tareas que alguien del equipo debe ejecutar. Este módulo permite que
esa conversión sea directa: con un par de clics, los compromisos se
transforman en tareas de proyecto, y la tarea queda vinculada a su
acta y compromiso de origen para trazabilidad.

Uso
===

Asociar un acta a un proyecto
-----------------------------

En el formulario del acta aparece el campo **Proyecto**. Seleccionarlo
marca el proyecto de referencia para los compromisos que se
conviertan en tareas.

Cada compromiso puede además tener su propio proyecto individual,
útil en reuniones que abarcan varios proyectos a la vez.

Convertir compromisos en tareas
-------------------------------

Desde el acta, el botón **Crear tareas de compromisos** abre un
asistente que:

1. Lista los compromisos aún no convertidos.
2. Permite seleccionar cuáles generar como tareas.
3. Permite elegir el proyecto destino (por defecto, el del acta).
4. Crea las tareas y las enlaza a sus compromisos.

Los compromisos ya convertidos no vuelven a aparecer en el asistente:
cada compromiso genera una sola tarea, evitando duplicados.

Seguimiento desde la tarea
--------------------------

En la tarea creada se muestra:

* El acta de origen
* El compromiso que le dio origen

Esto permite volver desde la tarea a su contexto: quién la solicitó,
en qué reunión y por qué.

Cuando la tarea se completa, el estado del compromiso puede
actualizarse manualmente desde el acta para cerrar el ciclo.

Créditos
========

Autores
-------

* Ivan Candelas

Mantenedor
----------

Ivan Candelas — <https://nxscore.mx>
