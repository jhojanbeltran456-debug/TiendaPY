# TiendaPy 🛒

Aplicación de consola en Python para controlar el **inventario y las ventas de una tienda de barrio**
(caso de estudio: tienda "Don Aurelio", Kennedy, Bogotá). Proyecto final.

## Problemas que resuelve

| Problema de Don Aurelio | Módulo de TiendaPy |
|---|---|
| Desabastecimiento inesperado | Alertas de stock agrupadas por proveedor (M3) |
| Errores de cálculo en totales y cambio | Carrito con subtotal, descuento, total y cambio automáticos (M2) |
| Productos sin rotación | Cierre del día: productos sin ventas (M4) |
| Pérdida del cuaderno | Persistencia en archivos de texto plano (M5) |
| Compras ineficientes | Alertas por proveedor: qué pedir y a quién |
| Sin cierre de caja | Total vendido, ticket promedio, más vendido, categorías (M4) |

## Requisitos

- Python 3.8 o superior
- Librería externa: [`tabulate`](https://pypi.org/project/tabulate/) (tablas en consola)

> Si `tabulate` no está instalada, el programa usa un formateador de tablas de respaldo y sigue funcionando.

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd tiendapy

# 2. Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python src/main.py
```

## Estructura del proyecto

```
tiendapy/
|-- README.md
|-- requirements.txt
|-- data/
|   |-- inventario.txt      # un producto por línea, campos separados por |
|   `-- ventas.txt          # una venta por línea: fecha|total|cod:cant;cod:cant
|-- src/
|   |-- main.py             # menú principal y flujo general
|   |-- inventario.py       # CRUD de productos
|   |-- ventas.py           # carrito, descuentos y cambio
|   |-- reportes.py         # alertas y cierre del día
|   |-- persistencia.py     # lectura y escritura de archivos
|   `-- validaciones.py     # captura segura de datos y excepciones de negocio
`-- tests/
    `-- test_tiendapy.py    # pruebas automáticas de los criterios de aceptación
```

## Formato de los archivos de datos

`data/inventario.txt`
```
LAC001|Leche entera 1L|Lacteos|4200.0|35|10|Alqueria
```
Campos: `codigo|nombre|categoria|precio|stock|stock_minimo|proveedor`

`data/ventas.txt`
```
2026-11-20|18400.0|LAC001:2;BEB003:1
```
Campos: `fecha|total|codigo:cantidad;codigo:cantidad`

## Reglas de negocio implementadas

- No se vende más que el stock disponible (se considera lo ya agregado al carrito).
- Precios, cantidades y stock mínimo deben ser mayores que cero.
- Descuento del 5 % si el subtotal es ≥ $50.000 y del 10 % si es ≥ $100.000.
- El pago no puede ser inferior al total; se permite reintentar.
- Los códigos de producto son únicos (se normalizan a mayúsculas).
- Stock en cero aparece como AGOTADO en las alertas.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas cubren los criterios CF-01 a CF-13 y CR-01 a CR-06, incluyendo una sesión de
consola completa simulada con entradas inválidas.

