"""Captura segura de datos y excepciones propias del negocio (CR-01, CR-02, CR-06)."""


class ErrorNegocio(Exception):
    """Violación de una regla de negocio de TiendaPy."""


class CodigoDuplicado(ErrorNegocio):
    pass


class ProductoNoEncontrado(ErrorNegocio):
    pass


class StockInsuficiente(ErrorNegocio):
    pass


class PagoInsuficiente(ErrorNegocio):
    pass


def leer_texto(mensaje, permitir_vacio=False):
    """Pide un texto no vacío (salvo que se permita vacío)."""
    while True:
        valor = input(mensaje).strip()
        if valor or permitir_vacio:
            return valor
        print("  [!] El campo no puede estar vacío.")


def leer_entero(mensaje, minimo=1):
    """Pide un entero >= minimo. Repite hasta que el dato sea válido."""
    while True:
        texto = input(mensaje).strip()
        try:
            valor = int(texto)
        except ValueError:
            print("  [!] Debe ingresar un número entero (sin letras ni decimales).")
            continue
        if valor < minimo:
            if minimo >= 1:
                print("  [!] El valor debe ser mayor que cero.")
            else:
                print(f"  [!] El valor debe ser mayor o igual a {minimo}.")
            continue
        return valor


def leer_flotante(mensaje):
    """Pide un número > 0 (acepta coma o punto decimal)."""
    while True:
        texto = input(mensaje).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("  [!] Debe ingresar un número válido.")
            continue
        if valor != valor or valor in (float("inf"), float("-inf")):
            print("  [!] Número no válido.")
            continue
        if valor <= 0:
            print("  [!] El valor debe ser mayor que cero.")
            continue
        return valor


def leer_opcion(mensaje, opciones):
    """Pide una opción dentro de un conjunto de cadenas válidas."""
    while True:
        valor = input(mensaje).strip()
        if valor in opciones:
            return valor
        print(f"  [!] Opción no válida. Elija entre: {', '.join(sorted(opciones))}")


def confirmar(mensaje):
    """Pregunta sí/no. Devuelve True si el usuario responde s/si."""
    while True:
        r = input(mensaje + " (s/n): ").strip().lower()
        if r in ("s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False
        print("  [!] Responda 's' o 'n'.")


def leer_codigo(mensaje):
    """Pide un código de producto normalizado (mayúsculas, sin '|' ni espacios)."""
    while True:
        valor = input(mensaje).strip().upper()
        if not valor:
            print("  [!] El código no puede estar vacío.")
        elif "|" in valor or ":" in valor or ";" in valor or " " in valor:
            print("  [!] El código no puede contener espacios ni los caracteres | : ;")
        else:
            return valor


def texto_seguro(valor):
    """Elimina el separador de persistencia de campos de texto libre."""
    return valor.replace("|", "/").replace("\n", " ").strip()
