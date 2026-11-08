"""Pruebas de los criterios de aceptación CF-01..CF-13 y CR-01..CR-06."""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)

import inventario as inv  # noqa: E402
import main  # noqa: E402
import persistencia  # noqa: E402
import reportes  # noqa: E402
import validaciones  # noqa: E402
import ventas  # noqa: E402
from validaciones import (  # noqa: E402
    CodigoDuplicado,
    ErrorNegocio,
    PagoInsuficiente,
    ProductoNoEncontrado,
    StockInsuficiente,
)

DATOS = os.path.join(SRC, "..", "data", "inventario.txt")


def inventario_base():
    return {
        "A1": dict(codigo="A1", nombre="Arroz", categoria="Abarrotes", precio=5000.0, stock=20, stock_minimo=5, proveedor="P1"),
        "B1": dict(codigo="B1", nombre="Gaseosa", categoria="Bebidas", precio=6000.0, stock=3, stock_minimo=5, proveedor="P2"),
        "C1": dict(codigo="C1", nombre="Cerveza", categoria="Bebidas", precio=3500.0, stock=0, stock_minimo=5, proveedor="P2"),
    }


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ruta_inv = os.path.join(self.tmp, "inventario.txt")
        self.ruta_ven = os.path.join(self.tmp, "ventas.txt")
        # Redirige las rutas por defecto para que ninguna prueba toque data/ real.
        self._p1 = mock.patch.object(persistencia, "RUTA_INVENTARIO", self.ruta_inv)
        self._p2 = mock.patch.object(persistencia, "RUTA_VENTAS", self.ruta_ven)
        self._p1.start()
        self._p2.start()

    def tearDown(self):
        self._p1.stop()
        self._p2.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestFuncionales(Base):
    def test_cf01_carga_inventario_de_ejemplo(self):
        datos = persistencia.cargar_inventario(DATOS)
        self.assertGreaterEqual(len(datos), 3)
        self.assertEqual(datos["LAC001"]["nombre"], "Leche entera 1L")
        self.assertEqual(datos["BEB003"]["stock"], 8)

    def test_cf03_registrar_y_rechazar_duplicado(self):
        i = inventario_base()
        inv.agregar_producto(i, "n1", "Nuevo", "Snacks", 1000, 5, 2, "P3")
        self.assertIn("N1", i)
        with self.assertRaisesRegex(CodigoDuplicado, "ya existe"):
            inv.agregar_producto(i, "A1", "Otro", "Aseo", 1000, 5, 2, "P3")

    def test_cf04_consultas_sin_fallar(self):
        i = inventario_base()
        self.assertEqual(inv.obtener_producto(i, "a1")["nombre"], "Arroz")
        with self.assertRaises(ProductoNoEncontrado):
            inv.obtener_producto(i, "ZZZ")
        self.assertEqual(len(inv.buscar_por_categoria(i, "bebidas")), 2)
        self.assertEqual(inv.buscar_por_categoria(i, "Inexistente"), [])

    def test_cf05_modificar_y_eliminar(self):
        i = inventario_base()
        inv.modificar_precio(i, "A1", 5500)
        inv.modificar_stock(i, "A1", 7)
        self.assertEqual((i["A1"]["precio"], i["A1"]["stock"]), (5500.0, 7))
        inv.eliminar_producto(i, "A1")
        self.assertNotIn("A1", i)
        with self.assertRaises(ProductoNoEncontrado):
            inv.eliminar_producto(i, "A1")

    def test_cf06_venta_multiproducto_con_detalle(self):
        i = inventario_base()
        c = ventas.nuevo_carrito()
        ventas.agregar_al_carrito(i, c, "A1", 2)
        ventas.agregar_al_carrito(i, c, "B1", 1)
        detalle = ventas.detalle_carrito(i, c)
        self.assertEqual(len(detalle), 2)
        self.assertEqual(ventas.calcular_total(i, c)[3], 16000.0)

    def test_cf07_descuentos_en_los_umbrales(self):
        casos = {49999: 0, 50000: 5, 99999: 5, 100000: 10, 250000: 10}
        for subtotal, pct in casos.items():
            self.assertEqual(ventas.calcular_descuento(subtotal)[0], pct, subtotal)
        self.assertEqual(ventas.calcular_descuento(50000)[1], 2500.0)
        self.assertEqual(ventas.calcular_descuento(100000)[1], 10000.0)

    def test_cf08_cambio_y_pago_insuficiente(self):
        self.assertEqual(ventas.calcular_cambio(18400, 20000), 1600.0)
        self.assertEqual(ventas.calcular_cambio(18400, 18400), 0.0)
        with self.assertRaises(PagoInsuficiente):
            ventas.calcular_cambio(18400, 18399)

    def test_cf09_venta_sobre_stock_rechazada_sin_cambiar_inventario(self):
        i = inventario_base()
        c = ventas.nuevo_carrito()
        with self.assertRaises(StockInsuficiente):
            ventas.agregar_al_carrito(i, c, "B1", 4)
        ventas.agregar_al_carrito(i, c, "B1", 2)
        with self.assertRaises(StockInsuficiente):  # el acumulado también cuenta
            ventas.agregar_al_carrito(i, c, "B1", 2)
        with self.assertRaises(StockInsuficiente):
            ventas.agregar_al_carrito(i, c, "C1", 1)  # agotado
        self.assertEqual(i["B1"]["stock"], 3)
        # Carrito adulterado: confirmar_venta debe fallar sin tocar nada
        malo = {"A1": 1, "B1": 99}
        with self.assertRaises(StockInsuficiente):
            ventas.confirmar_venta(i, malo, self.ruta_ven)
        self.assertEqual((i["A1"]["stock"], i["B1"]["stock"]), (20, 3))
        self.assertFalse(os.path.exists(self.ruta_ven))

    def test_cf10_confirmar_descuenta_stock_y_registra(self):
        i = inventario_base()
        c = {"A1": 2, "B1": 1}
        total = ventas.confirmar_venta(i, c, self.ruta_ven, fecha="2026-11-20")
        self.assertEqual(total, 16000.0)
        self.assertEqual((i["A1"]["stock"], i["B1"]["stock"]), (18, 2))
        with open(self.ruta_ven, encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "2026-11-20|16000.0|A1:2;B1:1")

    def test_cf11_alertas_por_proveedor_y_agotados(self):
        grupos = reportes.alertas_stock(inventario_base())
        self.assertEqual(list(grupos), ["P2"])  # A1 no está en alerta
        estados = {p["codigo"]: ag for p, ag in grupos["P2"]}
        self.assertEqual(estados, {"B1": False, "C1": True})

    def test_alerta_con_stock_igual_al_minimo(self):
        i = inventario_base()
        i["A1"]["stock"] = 5
        self.assertIn("P1", reportes.alertas_stock(i))

    def test_cf12_cierre_del_dia(self):
        i = inventario_base()
        hist = [
            {"fecha": "2026-11-20", "total": 10000.0, "items": [("A1", 2)]},
            {"fecha": "2026-11-20", "total": 12000.0, "items": [("A1", 1), ("B1", 1)]},
            {"fecha": "2026-11-19", "total": 99999.0, "items": [("C1", 9)]},
        ]
        r = reportes.cierre_del_dia(i, hist, fecha="2026-11-20")
        self.assertEqual(r["total_vendido"], 22000.0)
        self.assertEqual(r["n_ventas"], 2)
        self.assertEqual(r["ticket_promedio"], 11000.0)
        self.assertEqual(r["mas_vendido"], ("A1", "Arroz", 3))
        self.assertEqual([p["codigo"] for p in r["sin_ventas"]], ["C1"])
        self.assertEqual(set(r["categorias"]), {"Abarrotes", "Bebidas"})

    def test_cierre_sin_ventas_no_falla(self):
        r = reportes.cierre_del_dia(inventario_base(), [], fecha="2026-11-20")
        self.assertEqual((r["n_ventas"], r["ticket_promedio"], r["mas_vendido"]), (0, 0.0, None))

    def test_cf13_persistencia_entre_ejecuciones(self):
        i = inventario_base()
        c = {"A1": 3}
        ventas.confirmar_venta(i, c, self.ruta_ven, fecha="2026-11-20")
        self.assertTrue(persistencia.guardar_inventario(i, self.ruta_inv))
        recargado = persistencia.cargar_inventario(self.ruta_inv)
        self.assertEqual(recargado, i)
        self.assertEqual(recargado["A1"]["stock"], 17)
        hist = persistencia.cargar_ventas(self.ruta_ven)
        self.assertEqual(hist[0]["items"], [("A1", 3)])


class TestRobustez(Base):
    def _con_entradas(self, entradas, funcion, *args):
        salida = io.StringIO()
        with mock.patch("builtins.input", side_effect=entradas), contextlib.redirect_stdout(salida):
            return funcion(*args), salida.getvalue()

    def test_cr01_texto_donde_va_numero(self):
        v, out = self._con_entradas(["abc", "", "3.5", "7"], validaciones.leer_entero, "n: ")
        self.assertEqual(v, 7)
        self.assertIn("entero", out)
        v, _ = self._con_entradas(["hola", "nan", "1,5"], validaciones.leer_flotante, "p: ")
        self.assertEqual(v, 1.5)

    def test_cr02_cero_y_negativos_rechazados(self):
        v, _ = self._con_entradas(["0", "-4", "2"], validaciones.leer_entero, "n: ")
        self.assertEqual(v, 2)
        v, _ = self._con_entradas(["0", "-1.5", "-0", "9.9"], validaciones.leer_flotante, "p: ")
        self.assertEqual(v, 9.9)
        i = inventario_base()
        for args in [(0, 5, 2), (-1, 5, 2), (100, 0, 2), (100, -3, 2), (100, 5, 0)]:
            with self.assertRaises(ErrorNegocio):
                inv.agregar_producto(i, "Z9", "x", "Snacks", *args, "P")
        with self.assertRaises(ErrorNegocio):
            ventas.agregar_al_carrito(i, {}, "A1", 0)
        with self.assertRaises(ErrorNegocio):
            inv.modificar_precio(i, "A1", -5)

    def test_cr03_archivo_inexistente(self):
        datos, out = self._con_entradas([], persistencia.cargar_inventario, os.path.join(self.tmp, "no_existe.txt"))
        self.assertEqual(datos, {})
        self.assertEqual(persistencia.cargar_ventas(os.path.join(self.tmp, "no_existe.txt")), [])

    def test_cr04_lineas_corruptas_se_omiten(self):
        with open(self.ruta_inv, "w", encoding="utf-8") as f:
            f.write("OK1|Leche|Lacteos|4200.0|35|10|Alqueria\n")
            f.write("basura sin separadores\n")
            f.write("BAD|Algo|Aseo|precio_malo|5|2|P\n")
            f.write("NEG|Algo|Aseo|-100.0|5|2|P\n")
            f.write("\n")
            f.write("OK1|Duplicada|Lacteos|1.0|1|1|X\n")
            f.write("OK2|Arroz|Abarrotes|4800.0|40|15|Norte\n")
        datos, out = self._con_entradas([], persistencia.cargar_inventario, self.ruta_inv)
        self.assertEqual(sorted(datos), ["OK1", "OK2"])
        self.assertEqual(datos["OK1"]["nombre"], "Leche")
        self.assertEqual(out.count("omitida"), 4)
        with open(self.ruta_ven, "w", encoding="utf-8") as f:
            f.write("2026-11-20|1000.0|A1:2\nmal formato\n2026-11-20|x|A1:2\n2026-11-20|1.0|A1:cero\n")
        hist, out = self._con_entradas([], persistencia.cargar_ventas, self.ruta_ven)
        self.assertEqual(len(hist), 1)

    def test_cr05_archivos_cerrados_con_with(self):
        # Todos los open() del proyecto deben usarse con 'with'.
        for nombre in ("persistencia.py", "main.py", "inventario.py", "ventas.py", "reportes.py"):
            with open(os.path.join(SRC, nombre), encoding="utf-8") as f:
                for n, linea in enumerate(f, 1):
                    if "open(" in linea and "def " not in linea and "#" not in linea.split("open(")[0]:
                        self.assertIn("with ", linea, f"{nombre}:{n} usa open() sin with")

    def test_cr06_reglas_se_lanzan_con_raise(self):
        i = inventario_base()
        with self.assertRaises(CodigoDuplicado):
            inv.agregar_producto(i, "A1", "x", "Aseo", 1, 1, 1, "P")
        with self.assertRaises(StockInsuficiente):
            ventas.agregar_al_carrito(i, {}, "B1", 50)
        with self.assertRaises(PagoInsuficiente):
            ventas.calcular_cambio(100, 50)
        self.assertTrue(issubclass(StockInsuficiente, ErrorNegocio))


class TestSesionCompleta(Base):
    """Simula una sesión real de consola con errores de digitación (CF-01, CF-02, CR-01)."""

    def test_sesion_end_to_end(self):
        shutil.copy(DATOS, self.ruta_inv)
        entradas = [
            "x", "9",                              # opción inválida y luego inválida numérica
            "1", "1",                              # inventario > registrar
            "LAC001",                              # código duplicado -> reintenta
            "tst001", "Producto prueba", "Snacks", "abc", "-5", "2500", "quince", "10", "0", "4", "Proveedor X",
            "3", "TST001",                         # consultar por código
            "3", "NOEXISTE",                       # no existe: no debe fallar
            "0",                                   # volver
            "2",                                   # venta
            "1", "LAC001", "2",
            "1", "BEB003", "100",                  # excede stock -> rechazado
            "1", "ABA002", "5",                    # 5 x 14500 = 72500 + 8400 = 80900 -> 5%
            "4",                                   # cobrar
            "50000", "s",                          # pago insuficiente, reintentar
            "100000",                              # pago correcto
            "3",                                   # alertas
            "4",                                   # cierre del día
            "0",                                   # salir
        ]
        salida = io.StringIO()
        with mock.patch("builtins.input", side_effect=entradas), contextlib.redirect_stdout(salida):
            main.main()
        out = salida.getvalue()
        self.assertIn("16 producto(s) cargado(s)", out)
        self.assertIn("ya existe", out)
        self.assertIn("Stock insuficiente", out)
        self.assertIn("Pago insuficiente", out)
        self.assertIn("Descuento (5%)", out)
        self.assertIn("Cambio $23.145", out)       # 100000 - (80900 * 0.95 = 76855)
        self.assertIn("AGOTADO", out)
        self.assertIn("Ticket promedio", out)
        self.assertIn("Hasta pronto", out)
        # Persistencia tras 'cerrar' el programa
        guardado = persistencia.cargar_inventario(self.ruta_inv)
        self.assertEqual(guardado["LAC001"]["stock"], 33)
        self.assertEqual(guardado["ABA002"]["stock"], 13)
        self.assertEqual(guardado["BEB003"]["stock"], 8)
        self.assertIn("TST001", guardado)
        self.assertEqual(guardado["TST001"]["precio"], 2500.0)
        hist = persistencia.cargar_ventas(self.ruta_ven)
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["total"], 76855.0)


if __name__ == "__main__":
    unittest.main()
