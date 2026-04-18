[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Hour Wallet — Bolsas de Horas
=============================

Gestión de contratos o bolsas de horas vendidas a clientes: control de
saldo, vigencia, consumo, alertas automáticas y reportes periódicos.

Ideal para consultorías, equipos de soporte y proveedores de servicios
profesionales que venden horas por paquetes o suscripciones.

**Tabla de contenido**

* [Descripción](#descripción)
* [Uso](#uso)
  * [Crear una bolsa](#crear-una-bolsa)
  * [Registrar consumo](#registrar-consumo)
  * [Seguimiento y alertas](#seguimiento-y-alertas)
  * [Reportes para el cliente](#reportes-para-el-cliente)
* [Créditos](#créditos)

Descripción
===========

Una bolsa de horas representa un bloque de horas contratadas por un
cliente, con fecha de inicio, fecha de vencimiento y una cantidad total
de horas compradas. A medida que el equipo registra tiempo trabajado
contra esa bolsa, el sistema descuenta automáticamente del saldo.

La bolsa tiene un ciclo de vida claro: comienza en borrador, se
confirma para empezar a operar, y pasa a estados finales cuando se
agota, vence o se cierra manualmente. En cualquier momento se puede
reabrir si el cliente compra más horas o se extiende la vigencia.

El módulo emite avisos automáticos cuando una bolsa se aproxima a
saldo bajo, al vencimiento o al agotamiento total, para que el
responsable actúe a tiempo.

Uso
===

Crear una bolsa
---------------

Desde el menú **Bolsas de Horas → Operación → Bolsas**, crear un nuevo
registro indicando:

* Cliente
* Proyecto asociado (opcional)
* Tipo de bolsa
* Horas contratadas
* Fecha de inicio y vencimiento
* Si permite o no sobrepasar el total (sobreuso)

Al confirmar la bolsa queda activa y lista para recibir consumos.

Registrar consumo
-----------------

Los consumos se registran como partes de horas normales desde el
módulo de **Hojas de Tiempo**. El sistema sugiere automáticamente la
bolsa correcta según el cliente, proyecto o tarea a la que se carga
el tiempo.

El usuario puede cambiar la bolsa sugerida o fijar una distinta. Si
la carga excede el saldo disponible y la bolsa no permite sobreuso,
el sistema rechaza la operación con un mensaje claro.

Seguimiento y alertas
---------------------

En la vista de la bolsa se muestra en tiempo real:

* Horas consumidas
* Horas disponibles
* Porcentaje de consumo
* Indicador de saldo bajo

El sistema revisa diariamente todas las bolsas activas y:

* Marca como **agotada** las que llegan a cero.
* Marca como **vencida** las que pasan su fecha de expiración.
* Notifica a los responsables vía chatter y actividades cuando el
  saldo está bajo o próximo a vencer.

Cada alerta se envía una sola vez por bolsa para evitar ruido.

Reportes para el cliente
------------------------

Desde **Bolsas de Horas → Reportes → Reporte de consumo** se genera
un PDF con el detalle de horas trabajadas en un período, agrupadas
por bolsa, usuario o tarea según preferencia.

El reporte puede:

* **Previsualizarse** como PDF para revisión interna.
* **Enviarse por correo** al cliente mediante un compositor de
  mensajes que permite revisar destinatarios, asunto y cuerpo antes
  del envío. El PDF se adjunta automáticamente.

El envío nunca es automático: requiere la acción explícita del
usuario.

Créditos
========

Autores
-------

* Ivan Candelas

Mantenedor
----------

Ivan Candelas — <https://nxscore.mx>
