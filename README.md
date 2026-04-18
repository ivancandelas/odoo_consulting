[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)
[![Odoo 18](https://img.shields.io/badge/odoo-18.0-875A7B.svg)](https://www.odoo.com/documentation/18.0/)

odoo18_nexus
============

Conjunto de módulos para Odoo 18 enfocados en la operación interna de
consultorías y equipos de servicios profesionales: gestión de bolsas de
horas vendidas a clientes y documentación estructurada de reuniones
(actas, compromisos, seguimientos).

Los módulos están diseñados como piezas independientes que pueden
instalarse por separado según la necesidad del negocio.

**Tabla de contenido**

* [Módulos disponibles](#módulos-disponibles)
* [Instalación](#instalación)
* [Créditos](#créditos)

Módulos disponibles
===================

| Módulo | Descripción |
| --- | --- |
| [hour_wallet](hour_wallet) | Gestión de bolsas de horas vendidas a clientes: saldo, vigencia, alertas y reportes de consumo. |
| [meeting_minutes_base](meeting_minutes_base) | Actas de reunión con ciclo de vida, asistentes, compromisos y trazabilidad entre reuniones. |
| [meeting_minutes_project](meeting_minutes_project) | Integración de actas con proyectos: convierte compromisos en tareas. |
| [meeting_minutes_calendar](meeting_minutes_calendar) | Integración de actas con el calendario: el evento agenda, el acta documenta. |
| [meeting_minutes_report](meeting_minutes_report) | Reporte PDF profesional del acta de reunión. |
| [meeting_minutes_report_mail](meeting_minutes_report_mail) | Envío del acta al cliente por correo con el PDF adjunto. |

Los módulos de actas (`meeting_minutes_*`) siguen una arquitectura de
micro-módulos: el núcleo funciona de forma autónoma y cada integración
(proyectos, calendario, reportes, correo) se instala opcionalmente.

Instalación
===========

1. Clonar el repositorio dentro de la carpeta de addons de Odoo 18, o
   añadir su ruta al parámetro `addons-path` de la configuración.
2. Actualizar la lista de aplicaciones desde el menú **Aplicaciones**.
3. Instalar el módulo deseado desde la misma interfaz.

Cada módulo puede instalarse individualmente. Las dependencias se
resuelven automáticamente: por ejemplo, instalar
`meeting_minutes_report_mail` arrastra `meeting_minutes_report` y
`meeting_minutes_base`.

Créditos
========

Autores
-------

* Ivan Candelas

Mantenedor
----------

Este repositorio es mantenido por Ivan Candelas.

Para reportar incidencias o solicitar mejoras, contactar al mantenedor
a través del sitio web del autor: <https://nxscore.mx>.
