"""TiendaPy - menú principal y flujo general (M6, CF-01, CF-02)."""

import os
import sys

# Permite ejecutar tanto `python src/main.py` como `python main.py` desde src/.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import inventario as inv
import persistencia
import reportes
import ventas
from validaciones import (
    ErrorNegocio,
    confirmar,
    leer_codigo,
    leer_entero,
    leer_flotante,
    leer_opcion,
    leer_texto,
)

try:
    from tabulate import tabulate
except ImportError:  # Respaldo mínimo si no se instaló la dependencia.
    def tabulate(filas, headers=(), tablefmt=None, **_):
        filas = [list(map(str, f)) for f in filas]
        headers = list(map(str, headers))
        anchos = [max(len(str(x)) for x in col) for col in zip(headers, *filas)] if filas else [len(h) for h in headers]
        linea = lambda fila: " | ".join(c.ljust(a) for c, a in zip(fila, anchos))
        sep = "-+-".join("-" * a for a in anchos)
        return "\n".join([linea(headers), sep] + [linea(f) for f in filas])


def cop(valor):
    """Formatea un valor en pesos colombianos: $1.234.567"""
    return "$" + f"{valor:,.0f}".replace(",", ".")


def mostrar_productos(productos):
    if not productos:
        print("  (sin resultados)")
        return
    filas = [
        (p["codigo"], p["nombre"], p["categoria"], cop(p["precio"]), p["stock"], p["stock_minimo"], p["proveedor"])
        for p in productos
    ]
    print(tabulate(filas, headers=["Código", "Nombre", "Categoría", "Precio", "Stock", "Mín.", "Proveedor"], tablefmt="simple"))


# ---------------------------------------------------------------- Inventario
def menu_inventario(inventario):
    while True:
        print("\n--- GESTIÓN DE INVENTARIO ---")
        print("1. Registrar producto")
        print("2. Listar todos los productos")
        print("3. Consultar por código")
        print("4. Consultar por categoría")
        print("5. Modificar precio")
        print("6. Modificar stock")
        print("7. Eliminar producto")
        print("0. Volver")
        op = leer_opcion("Opción: ", {"0", "1", "2", "3", "4", "5", "6", "7"})
        try:
            if op == "0":
                return
            elif op == "1":
                registrar_producto(inventario)
            elif op == "2":
                mostrar_productos(sorted(inventario.values(), key=lambda p: p["codigo"]))
            elif op == "3":
                codigo = leer_codigo("Código: ")
                mostrar_productos([inv.obtener_producto(inventario, codigo)])
            elif op == "4":
                print("Categorías sugeridas:", ", ".join(inv.CATEGORIAS))
                cat = leer_texto("Categoría: ")
                resultado = inv.buscar_por_categoria(inventario, cat)
                if not resultado:
                    print(f"  No hay productos en la categoría '{cat}'.")
                else:
                    mostrar_productos(resultado)
            elif op == "5":
                codigo = leer_codigo("Código del producto: ")
                p = inv.obtener_producto(inventario, codigo)
                print(f"  {p['nombre']} - precio actual {cop(p['precio'])}")
                inv.modificar_precio(inventario, codigo, leer_flotante("Nuevo precio (COP): "))
                print("  Precio actualizado.")
            elif op == "6":
                codigo = leer_codigo("Código del producto: ")
                p = inv.obtener_producto(inventario, codigo)
                print(f"  {p['nombre']} - stock actual {p['stock']}")
                inv.modificar_stock(inventario, codigo, leer_entero("Nuevo stock (0 = agotado): ", minimo=0))
                print("  Stock actualizado.")
            elif op == "7":
                codigo = leer_codigo("Código del producto: ")
                p = inv.obtener_producto(inventario, codigo)
                if confirmar(f"¿Eliminar '{p['nombre']}'?"):
                    inv.eliminar_producto(inventario, codigo)
                    print("  Producto eliminado.")
                else:
                    print("  Operación cancelada.")
        except ErrorNegocio as error:  # CR-06: las reglas se señalan con raise y se capturan aquí
            print(f"  [!] {error}")


def registrar_producto(inventario):
    print("\nNuevo producto")
    while True:
        codigo = leer_codigo("Código único (ej. LAC001): ")
        if codigo in inventario:
            print(f"  [!] El código '{codigo}' ya existe. Intente con otro.")
            continue
        break
    nombre = leer_texto("Nombre: ")
    print("Categorías sugeridas:", ", ".join(inv.CATEGORIAS))
    categoria = leer_texto("Categoría: ")
    precio = leer_flotante("Precio de venta (COP): ")
    stock = leer_entero("Stock inicial: ")
    minimo = leer_entero("Stock mínimo: ")
    proveedor = leer_texto("Proveedor: ")
    inv.agregar_producto(inventario, codigo, nombre, categoria, precio, stock, minimo, proveedor)
    print("  Producto registrado.")


# -------------------------------------------------------------------- Ventas
def menu_venta(inventario):
    carrito = ventas.nuevo_carrito()
    print("\n--- NUEVA VENTA ---")
    while True:
        print("\n1. Agregar producto  2. Quitar producto  3. Ver carrito  4. Cobrar  0. Cancelar venta")
        op = leer_opcion("Opción: ", {"0", "1", "2", "3", "4"})
        try:
            if op == "0":
                if not carrito or confirmar("¿Cancelar la venta en curso?"):
                    print("  Venta cancelada. El inventario no cambió.")
                    return
            elif op == "1":
                codigo = leer_codigo("Código del producto: ")
                p = inv.obtener_producto(inventario, codigo)
                print(f"  {p['nombre']} - {cop(p['precio'])} - stock {p['stock']}")
                cantidad = leer_entero("Cantidad: ")
                ventas.agregar_al_carrito(inventario, carrito, codigo, cantidad)
                print("  Agregado al carrito.")
            elif op == "2":
                ventas.quitar_del_carrito(carrito, leer_codigo("Código a quitar: "))
                print("  Producto quitado.")
            elif op == "3":
                mostrar_carrito(inventario, carrito)
            elif op == "4":
                if cobrar(inventario, carrito):
                    return
        except ErrorNegocio as error:
            print(f"  [!] {error}")


def mostrar_carrito(inventario, carrito):
    if not carrito:
        print("  El carrito está vacío.")
        return
    filas = [(c, n, q, cop(pu), cop(v)) for c, n, q, pu, v in ventas.detalle_carrito(inventario, carrito)]
    print(tabulate(filas, headers=["Código", "Producto", "Cant.", "Precio", "Valor"], tablefmt="simple"))
    subtotal, pct, desc, total = ventas.calcular_total(inventario, carrito)
    print(f"\n  Subtotal:  {cop(subtotal)}")
    print(f"  Descuento ({pct}%): -{cop(desc)}")
    print(f"  TOTAL:     {cop(total)}")


def cobrar(inventario, carrito):
    """Devuelve True si la venta se completó."""
    if not carrito:
        print("  [!] El carrito está vacío.")
        return False
    mostrar_carrito(inventario, carrito)
    _, _, _, total = ventas.calcular_total(inventario, carrito)
    while True:
        pago = leer_flotante("\nPago recibido (COP): ")
        try:
            cambio = ventas.calcular_cambio(total, pago)
            break
        except ErrorNegocio as error:
            print(f"  [!] {error}")
            if not confirmar("¿Reintentar el pago?"):
                print("  Cobro cancelado; el carrito se conserva.")
                return False
    ventas.confirmar_venta(inventario, carrito)
    print(f"\n  Venta registrada. Total {cop(total)} | Pago {cop(pago)} | Cambio {cop(cambio)}")
    if persistencia.guardar_inventario(inventario):
        print("  Inventario guardado.")
    return True


# ------------------------------------------------------------------ Reportes
def mostrar_alertas(inventario):
    grupos = reportes.alertas_stock(inventario)
    if not grupos:
        print("\n  Sin alertas: todos los productos están por encima de su stock mínimo.")
        return
    print("\n--- ALERTAS DE STOCK (pedido por proveedor) ---")
    for proveedor, items in grupos.items():
        print(f"\nProveedor: {proveedor}")
        filas = [
            (p["codigo"], p["nombre"], p["stock"], p["stock_minimo"], "AGOTADO" if agotado else "Bajo")
            for p, agotado in items
        ]
        print(tabulate(filas, headers=["Código", "Producto", "Stock", "Mín.", "Estado"], tablefmt="simple"))


def mostrar_cierre(inventario):
    historial = persistencia.cargar_ventas()
    r = reportes.cierre_del_dia(inventario, historial)
    print(f"\n--- CIERRE DEL DÍA {r['fecha']} ---")
    print(f"  Total vendido:     {cop(r['total_vendido'])}")
    print(f"  Número de ventas:  {r['n_ventas']}")
    print(f"  Ticket promedio:   {cop(r['ticket_promedio'])}")
    if r["mas_vendido"]:
        cod, nombre, cant = r["mas_vendido"]
        print(f"  Más vendido:       {nombre} ({cod}) - {cant} unidades")
    else:
        print("  Más vendido:       (sin ventas hoy)")
    if r["categorias"]:
        filas = [(c, d["unidades"]) for c, d in sorted(r["categorias"].items())]
        print("\n  Categorías con movimiento:")
        print(tabulate(filas, headers=["Categoría", "Unidades"], tablefmt="simple"))
    if r["sin_ventas"]:
        print("\n  Productos sin ventas hoy:")
        mostrar_productos(sorted(r["sin_ventas"], key=lambda p: p["codigo"]))


# --------------------------------------------------------------------- Menú
def menu_principal(inventario):
    while True:
        print("\n=========== TIENDAPY ===========")
        print("1. Gestión de inventario")
        print("2. Nueva venta")
        print("3. Alertas de stock")
        print("4. Cierre del día")
        print("5. Guardar inventario")
        print("0. Salir")
        op = leer_opcion("Opción: ", {"0", "1", "2", "3", "4", "5"})
        if op == "0":
            if persistencia.guardar_inventario(inventario):
                print("Inventario guardado. ¡Hasta pronto!")
            return
        elif op == "1":
            menu_inventario(inventario)
        elif op == "2":
            menu_venta(inventario)
        elif op == "3":
            mostrar_alertas(inventario)
        elif op == "4":
            mostrar_cierre(inventario)
        elif op == "5":
            if persistencia.guardar_inventario(inventario):
                print("  Inventario guardado.")


def main():
    print("Cargando inventario...")
    inventario = persistencia.cargar_inventario()
    print(f"  {len(inventario)} producto(s) cargado(s).")
    try:
        menu_principal(inventario)
    except (KeyboardInterrupt, EOFError):
        print("\nInterrumpido. Guardando inventario...")
        persistencia.guardar_inventario(inventario)


if __name__ == "__main__":
    main()
