"""Lectura y escritura de archivos de texto plano (CF-13, CR-03, CR-04, CR-05)."""

import os

RUTA_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
RUTA_INVENTARIO = os.path.join(RUTA_BASE, "inventario.txt")
RUTA_VENTAS = os.path.join(RUTA_BASE, "ventas.txt")

CAMPOS_PRODUCTO = 7


def _parsear_producto(linea):
    """Convierte una línea en (codigo, dict). Lanza ValueError si está corrupta."""
    partes = linea.split("|")
    if len(partes) != CAMPOS_PRODUCTO:
        raise ValueError(f"se esperaban {CAMPOS_PRODUCTO} campos y hay {len(partes)}")
    codigo, nombre, categoria, precio, stock, stock_min, proveedor = (p.strip() for p in partes)
    if not codigo or not nombre or not categoria or not proveedor:
        raise ValueError("hay campos de texto vacíos")
    precio = float(precio)
    stock = int(stock)
    stock_min = int(stock_min)
    if precio <= 0:
        raise ValueError("precio no positivo")
    if stock < 0 or stock_min < 0:
        raise ValueError("stock negativo")
    return codigo, {
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio,
        "stock": stock,
        "stock_minimo": stock_min,
        "proveedor": proveedor,
    }


def cargar_inventario(ruta=None):
    """Carga el inventario. Devuelve dict {codigo: producto}.

    - Si el archivo no existe, informa y devuelve un inventario vacío (CR-03).
    - Las líneas corruptas o duplicadas se omiten con advertencia (CR-04).
    """
    ruta = ruta or RUTA_INVENTARIO
    inventario = {}
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            for n, linea in enumerate(archivo, start=1):
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    codigo, producto = _parsear_producto(linea)
                except ValueError as error:
                    print(f"  [!] Línea {n} omitida en inventario ({error}): {linea[:50]}")
                    continue
                if codigo in inventario:
                    print(f"  [!] Línea {n} omitida: código duplicado '{codigo}'.")
                    continue
                inventario[codigo] = producto
    except FileNotFoundError:
        print(f"  [i] No se encontró {os.path.basename(ruta)}; se inicia con inventario vacío.")
    except OSError as error:
        print(f"  [!] No se pudo leer el inventario ({error}); se inicia vacío.")
    return inventario


def guardar_inventario(inventario, ruta=None):
    """Guarda el inventario completo, un producto por línea. Devuelve True si tuvo éxito."""
    ruta = ruta or RUTA_INVENTARIO
    try:
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            for p in inventario.values():
                archivo.write(
                    f"{p['codigo']}|{p['nombre']}|{p['categoria']}|{float(p['precio'])}|"
                    f"{p['stock']}|{p['stock_minimo']}|{p['proveedor']}\n"
                )
        return True
    except OSError as error:
        print(f"  [!] No se pudo guardar el inventario: {error}")
        return False


def registrar_venta(fecha, total, items, ruta=None):
    """Agrega una venta al final de ventas.txt.

    items: lista de (codigo, cantidad). Formato: fecha|total|cod:cant;cod:cant
    """
    ruta = ruta or RUTA_VENTAS
    detalle = ";".join(f"{cod}:{cant}" for cod, cant in items)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        with open(ruta, "a", encoding="utf-8") as archivo:
            archivo.write(f"{fecha}|{float(total)}|{detalle}\n")
        return True
    except OSError as error:
        print(f"  [!] No se pudo registrar la venta en el historial: {error}")
        return False


def cargar_ventas(ruta=None):
    """Lee el historial. Devuelve lista de dicts {fecha, total, items:[(cod, cant)]}."""
    ruta = ruta or RUTA_VENTAS
    ventas = []
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            for n, linea in enumerate(archivo, start=1):
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    partes = linea.split("|")
                    if len(partes) != 3:
                        raise ValueError("número de campos incorrecto")
                    fecha, total, detalle = partes
                    total = float(total)
                    items = []
                    for par in detalle.split(";"):
                        cod, cant = par.split(":")
                        cant = int(cant)
                        if not cod or cant <= 0:
                            raise ValueError("detalle inválido")
                        items.append((cod, cant))
                    if not fecha or not items:
                        raise ValueError("venta vacía")
                    ventas.append({"fecha": fecha, "total": total, "items": items})
                except ValueError as error:
                    print(f"  [!] Línea {n} omitida en ventas ({error}): {linea[:50]}")
    except FileNotFoundError:
        pass  # Sin historial todavía: no es un error.
    except OSError as error:
        print(f"  [!] No se pudo leer el historial de ventas: {error}")
    return ventas
