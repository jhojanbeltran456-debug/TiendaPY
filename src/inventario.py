"""CRUD de productos (módulo M1: CF-03, CF-04, CF-05)."""

from validaciones import (
    CodigoDuplicado,
    ErrorNegocio,
    ProductoNoEncontrado,
    texto_seguro,
)

CATEGORIAS = ["Lacteos", "Bebidas", "Aseo", "Abarrotes", "Snacks"]


def agregar_producto(inventario, codigo, nombre, categoria, precio, stock, stock_minimo, proveedor):
    """Registra un producto nuevo. Lanza CodigoDuplicado o ErrorNegocio."""
    codigo = codigo.strip().upper()
    if codigo in inventario:
        raise CodigoDuplicado(f"El código '{codigo}' ya existe: {inventario[codigo]['nombre']}.")
    if precio <= 0:
        raise ErrorNegocio("El precio debe ser mayor que cero.")
    if stock <= 0:
        raise ErrorNegocio("El stock inicial debe ser mayor que cero.")
    if stock_minimo <= 0:
        raise ErrorNegocio("El stock mínimo debe ser mayor que cero.")
    producto = {
        "codigo": codigo,
        "nombre": texto_seguro(nombre),
        "categoria": texto_seguro(categoria),
        "precio": float(precio),
        "stock": int(stock),
        "stock_minimo": int(stock_minimo),
        "proveedor": texto_seguro(proveedor),
    }
    inventario[codigo] = producto
    return producto


def obtener_producto(inventario, codigo):
    """Devuelve el producto o lanza ProductoNoEncontrado."""
    codigo = codigo.strip().upper()
    if codigo not in inventario:
        raise ProductoNoEncontrado(f"No existe un producto con código '{codigo}'.")
    return inventario[codigo]


def buscar_por_categoria(inventario, categoria):
    """Lista de productos de una categoría (sin distinguir mayúsculas ni tildes simples)."""
    objetivo = _normalizar(categoria)
    return [p for p in inventario.values() if _normalizar(p["categoria"]) == objetivo]


def modificar_precio(inventario, codigo, nuevo_precio):
    if nuevo_precio <= 0:
        raise ErrorNegocio("El precio debe ser mayor que cero.")
    producto = obtener_producto(inventario, codigo)
    producto["precio"] = float(nuevo_precio)
    return producto


def modificar_stock(inventario, codigo, nuevo_stock):
    """Fija el stock. Se permite 0 al ajustar (producto agotado) pero no negativos."""
    if nuevo_stock < 0:
        raise ErrorNegocio("El stock no puede ser negativo.")
    producto = obtener_producto(inventario, codigo)
    producto["stock"] = int(nuevo_stock)
    return producto


def eliminar_producto(inventario, codigo):
    obtener_producto(inventario, codigo)
    return inventario.pop(codigo.strip().upper())


def _normalizar(texto):
    reemplazos = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return texto.strip().translate(reemplazos).lower()
