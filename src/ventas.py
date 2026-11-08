"""Carrito, descuentos, pago y cambio (módulo M2: CF-06 a CF-10)."""

from datetime import date

import persistencia
from validaciones import ErrorNegocio, PagoInsuficiente, ProductoNoEncontrado, StockInsuficiente

UMBRAL_DESCUENTO_10 = 100_000
UMBRAL_DESCUENTO_5 = 50_000


def nuevo_carrito():
    """Un carrito es un dict {codigo: cantidad}."""
    return {}


def agregar_al_carrito(inventario, carrito, codigo, cantidad):
    """Agrega unidades al carrito validando existencia y stock acumulado (CF-09)."""
    codigo = codigo.strip().upper()
    if cantidad <= 0:
        raise ErrorNegocio("La cantidad debe ser mayor que cero.")
    if codigo not in inventario:
        raise ProductoNoEncontrado(f"No existe un producto con código '{codigo}'.")
    producto = inventario[codigo]
    ya_en_carrito = carrito.get(codigo, 0)
    if ya_en_carrito + cantidad > producto["stock"]:
        disponible = producto["stock"] - ya_en_carrito
        raise StockInsuficiente(
            f"Stock insuficiente de '{producto['nombre']}': "
            f"solicitado {cantidad}, disponible {max(disponible, 0)}."
        )
    carrito[codigo] = ya_en_carrito + cantidad
    return carrito


def quitar_del_carrito(carrito, codigo):
    codigo = codigo.strip().upper()
    if codigo not in carrito:
        raise ProductoNoEncontrado(f"El producto '{codigo}' no está en el carrito.")
    del carrito[codigo]


def detalle_carrito(inventario, carrito):
    """Lista de filas (codigo, nombre, cantidad, precio_unit, valor)."""
    filas = []
    for codigo, cantidad in carrito.items():
        p = inventario[codigo]
        filas.append((codigo, p["nombre"], cantidad, p["precio"], p["precio"] * cantidad))
    return filas


def calcular_subtotal(inventario, carrito):
    return sum(fila[4] for fila in detalle_carrito(inventario, carrito))


def calcular_descuento(subtotal):
    """5 % desde $50.000 y 10 % desde $100.000 (CF-07). Devuelve (porcentaje, valor)."""
    if subtotal >= UMBRAL_DESCUENTO_10:
        porcentaje = 10
    elif subtotal >= UMBRAL_DESCUENTO_5:
        porcentaje = 5
    else:
        porcentaje = 0
    return porcentaje, round(subtotal * porcentaje / 100, 2)


def calcular_total(inventario, carrito):
    """Devuelve (subtotal, porcentaje_descuento, descuento, total)."""
    subtotal = calcular_subtotal(inventario, carrito)
    porcentaje, descuento = calcular_descuento(subtotal)
    return subtotal, porcentaje, descuento, round(subtotal - descuento, 2)


def calcular_cambio(total, pago):
    """Lanza PagoInsuficiente si el pago no cubre el total (CF-08)."""
    if pago < total:
        raise PagoInsuficiente(
            f"Pago insuficiente: faltan ${total - pago:,.0f} COP.".replace(",", ".")
        )
    return round(pago - total, 2)


def confirmar_venta(inventario, carrito, ruta_ventas=None, fecha=None):
    """Descuenta el stock y registra la venta (CF-10).

    Valida TODO antes de modificar nada, así el inventario no cambia si algo falla (CF-09).
    Devuelve el total cobrado.
    """
    if not carrito:
        raise ErrorNegocio("El carrito está vacío.")
    for codigo, cantidad in carrito.items():
        if codigo not in inventario:
            raise ProductoNoEncontrado(f"El producto '{codigo}' ya no existe.")
        if cantidad > inventario[codigo]["stock"]:
            raise StockInsuficiente(
                f"Stock insuficiente de '{inventario[codigo]['nombre']}' "
                f"(disponible {inventario[codigo]['stock']})."
            )
    _, _, _, total = calcular_total(inventario, carrito)
    for codigo, cantidad in carrito.items():
        inventario[codigo]["stock"] -= cantidad
    fecha = fecha or date.today().isoformat()
    persistencia.registrar_venta(fecha, total, list(carrito.items()), ruta_ventas)
    return total
