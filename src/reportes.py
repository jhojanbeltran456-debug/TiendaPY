"""Alertas de stock y cierre del día (módulos M3 y M4: CF-11, CF-12)."""

from collections import defaultdict
from datetime import date


def alertas_stock(inventario):
    """Productos con stock <= mínimo agrupados por proveedor (CF-11).

    Devuelve {proveedor: [(producto, agotado_bool), ...]} ordenado por proveedor.
    """
    grupos = defaultdict(list)
    for p in inventario.values():
        if p["stock"] <= p["stock_minimo"]:
            grupos[p["proveedor"]].append((p, p["stock"] == 0))
    return {prov: sorted(items, key=lambda x: x[0]["codigo"]) for prov, items in sorted(grupos.items())}


def cierre_del_dia(inventario, ventas, fecha=None):
    """Calcula las métricas del cierre del día (CF-12).

    ventas: lista del historial completo; se filtra por fecha (hoy por defecto).
    """
    fecha = fecha or date.today().isoformat()
    del_dia = [v for v in ventas if v["fecha"] == fecha]

    total_vendido = sum(v["total"] for v in del_dia)
    n_ventas = len(del_dia)
    ticket_promedio = total_vendido / n_ventas if n_ventas else 0.0

    unidades = defaultdict(int)
    for v in del_dia:
        for codigo, cantidad in v["items"]:
            unidades[codigo] += cantidad

    mas_vendido = None
    if unidades:
        codigo_top = max(unidades, key=lambda c: (unidades[c], c))
        nombre = inventario[codigo_top]["nombre"] if codigo_top in inventario else "(producto eliminado)"
        mas_vendido = (codigo_top, nombre, unidades[codigo_top])

    sin_ventas = [p for c, p in inventario.items() if c not in unidades]

    categorias = defaultdict(lambda: {"unidades": 0})
    for codigo, cant in unidades.items():
        if codigo in inventario:
            categorias[inventario[codigo]["categoria"]]["unidades"] += cant

    return {
        "fecha": fecha,
        "total_vendido": total_vendido,
        "n_ventas": n_ventas,
        "ticket_promedio": ticket_promedio,
        "mas_vendido": mas_vendido,
        "sin_ventas": sin_ventas,
        "categorias": dict(categorias),
    }
