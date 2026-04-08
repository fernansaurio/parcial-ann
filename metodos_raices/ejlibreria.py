# El siguiente codigo permite calcular la raiz de una funcion por diferentes metodos
# El codigo permite ingresarlo directamente desde consola utilizando una sintaxis en especifico, igualando las variables a sus valores
# Si no se necesita esa funcion desde consola, se pueden usar los valores fijos dentro del codigo
#Fernando José Padilla Cruz - PC24039
import sys
import time
import ctypes
import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, lambdify, diff, sympify
from sympy.parsing.latex import parse_latex

def main():
    #Fernando José Padilla Cruz - PC24039
    # =========================================================================
    # 📦 CAJÓN DE CONFIGURACIÓN RÁPIDA 📦
    # =========================================================================
    LEER_DESDE_CONSOLA = True

    # Valores fijos (Solo se utilizan si LEER_DESDE_CONSOLA = False)
    fijo_ec = "\\cos(x) - 0.5"   # Ecuación de ejemplo en LaTeX
    fijo_metodo = "solo_graficar" # Opciones: biseccion, secante, etc., o "solo_graficar"
    fijo_p1 = -5.0
    fijo_p2 = 5.0
    fijo_tol = 1e-6      # Tolerancia por defecto
    fijo_max_iter = 100  # Máximo de iteraciones por defecto
    fijo_grafica = True
    fijo_time = True
    # =========================================================================

    # 1. Asignación de variables (Consola vs Fijos)
    if LEER_DESDE_CONSOLA:
        args_dict = {}
        for arg in sys.argv[1:]:
            if '=' in arg:
                clave, valor = arg.split('=', 1)
                args_dict[clave.lower()] = valor
                
        if 'ec' not in args_dict:
            print('Uso para calcular: python3 ejlibreria.py ec="x^2 - 4" metodo=biseccion p1=0 p2=5 grafica=true')
            print('Uso solo graficar: python3 ejlibreria.py ec="\\cos(x) - 0.5" p1=-5 p2=5 grafica=true')
            print('Metodos disponibles: biseccion, falsa_posicion, newton_raphson, secante, punto_fijo')
            sys.exit(1)

        latex_eq = args_dict['ec']
        mostrar_grafica = args_dict.get('grafica', 'false').lower() == 'true'
        contar_tiempo = args_dict.get('time', 'false').lower() == 'true'
        
        # Si no hay método pero sí grafica=true, asumimos que solo quiere ver la gráfica
        if 'metodo' not in args_dict:
            if mostrar_grafica:
                metodo = "solo_graficar"
            else:
                print("Error: Debes especificar un 'metodo' o habilitar 'grafica=true'.")
                sys.exit(1)
        else:
            metodo = args_dict['metodo'].lower()
        
        try:
            # Límites para la gráfica o el método
            p1 = float(args_dict.get('p1', -10.0))
            p2 = float(args_dict.get('p2', 10.0))
            tol = float(args_dict.get('tol', 1e-6))
            max_iter = int(args_dict.get('iter', 100))
        except ValueError:
            print("Error: p1, p2, tol y iter deben ser valores numéricos.")
            sys.exit(1)
            
    else:
        print("Aviso: Ejecutando con valores fijos en el código.")
        latex_eq = fijo_ec
        metodo = fijo_metodo
        p1 = fijo_p1
        p2 = fijo_p2
        tol = fijo_tol
        max_iter = fijo_max_iter
        mostrar_grafica = fijo_grafica
        contar_tiempo = fijo_time
    #Fernando José Padilla Cruz - PC24039
    # 2. Parsear la ecuación de LaTeX
    x = symbols('x')
    try:
        expr = parse_latex(latex_eq)
    except Exception as e:
        print(f"Error al procesar LaTeX. Intentando como texto normal...")
        try:
            expr = sympify(latex_eq)
        except Exception as e2:
            print(f"Error fatal al leer la ecuación: {e2}")
            sys.exit(1)
    
    # 3. Generar lambdas usando la librería 'math', honestamente no recuerdo que era lambda pero lo puso gemini deah
    _f_py = lambdify(x, expr, 'math')
    
    # Solo necesitamos las derivadas si vamos a calcular raíces (ahorra tiempo si es solo gráfica)
    if metodo != "solo_graficar":
        expr_diff = diff(expr, x)
        _df_py = lambdify(x, expr_diff, 'math')
        g_expr = x - expr
        _g_py = lambdify(x, g_expr, 'math')

    # 4. WRAPPERS: Escudos contra errores de dominio
    def f_py(val):
        try:
            return float(_f_py(val))
        except Exception:
            return float('nan')

    if metodo != "solo_graficar":
        def df_py(val):
            try:
                return float(_df_py(val))
            except Exception:
                return float('nan')

        def g_py(val):
            try:
                return float(_g_py(val))
            except Exception:
                return float('nan')

    raiz = None

    # Si NO es solo gráfica, cargamos C++ y calculamos, esto lo agregue porque me daba una paja buscar puntos por mi cuenta
    if metodo != "solo_graficar":
        # 5. Configurar C++ (ctypes)
        try:
            lib = ctypes.CDLL('./libraices.so')
        except OSError:
            print("Error: No se encontro 'libraices.so'. Compila el archivo C++ primero.")
            sys.exit(1)

        CMPFUNC = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_double)
        
        c_f = CMPFUNC(f_py)
        c_df = CMPFUNC(df_py)
        c_g = CMPFUNC(g_py)

        for func in [lib.biseccion, lib.falsa_posicion, lib.newton_raphson, lib.secante, lib.punto_fijo]:
            func.restype = ctypes.c_double

        # 6. Ejecución y medición
        start_time = time.perf_counter()
        iteraciones = ctypes.c_int(0)

        if metodo == 'biseccion':
            raiz = lib.biseccion(c_f, ctypes.c_double(p1), ctypes.c_double(p2), ctypes.c_double(tol), ctypes.c_int(max_iter), ctypes.byref(iteraciones))
        elif metodo == 'falsa_posicion':
            raiz = lib.falsa_posicion(c_f, ctypes.c_double(p1), ctypes.c_double(p2), ctypes.c_double(tol), ctypes.c_int(max_iter), ctypes.byref(iteraciones))
        elif metodo == 'newton_raphson':
            raiz = lib.newton_raphson(c_f, c_df, ctypes.c_double(p1), ctypes.c_double(tol), ctypes.c_int(max_iter), ctypes.byref(iteraciones))
        elif metodo == 'secante':
            raiz = lib.secante(c_f, ctypes.c_double(p1), ctypes.c_double(p2), ctypes.c_double(tol), ctypes.c_int(max_iter), ctypes.byref(iteraciones))
        elif metodo == 'punto_fijo':
            raiz = lib.punto_fijo(c_g, ctypes.c_double(p1), ctypes.c_double(tol), ctypes.c_int(max_iter), ctypes.byref(iteraciones))
        else:
            print(f"Método desconocido: {metodo}")
            sys.exit(1)
            
        end_time = time.perf_counter() #pa los obsesionados con el tiempo
        iteraciones = iteraciones.value if hasattr(iteraciones, 'value') else 'N/A'

        # 7. Imprimir resultados de la raíz
        print(f"\n--- RESULTADOS ---")
        print(f"Ecuación: f(x) = {expr}")
        print(f"Método  : {metodo}")
        print(f"Iteraciones: {iteraciones}")
        
        if np.isnan(raiz):
            print(f"Estado  : FALLO tras {max_iter} iteraciones o intervalo inválido.")
        else:
            print(f"Raíz    : x = {raiz:.6f}")
            print(f"Error f(x): {f_py(raiz):.2e}")
            print(f"Tolerancia usada: {tol}")
        
        if contar_tiempo:
            print(f"Tiempo C++: {(end_time - start_time) * 1000:.6f} ms")
        print("------------------\n")
    else:
        # Modo Solo Gráfica
        print(f"\n--- MODO VISTA PREVIA (SOLO GRÁFICA) ---")
        print(f"Ecuación: f(x) = {expr}")
        print(f"Rango de visualización: [{p1}, {p2}]")
        print("----------------------------------------\n")

    # 8. Graficar dinámicamente
    if mostrar_grafica:
        # Determinar el rango X para la gráfica
        if metodo != "solo_graficar" and raiz is not None and not np.isnan(raiz):
            r_val = float(raiz)
            rango = max(5.0, abs(p2 - p1) if metodo in ['biseccion', 'falsa_posicion'] else 5.0)
            x_vals = np.linspace(r_val - rango, r_val + rango, 400)
        else:
            # Si solo estamos graficando, usamos los p1 y p2 que pasó el usuario (o los por defecto)
            x_vals = np.linspace(p1, p2, 500)
        
        # Generamos los puntos Y de forma segura
        y_vals = [f_py(val) for val in x_vals]
        
        plt.figure(figsize=(8, 5))
        plt.plot(x_vals, y_vals, label=f'$f(x) = {expr}$')
        plt.axhline(0, color='black', linewidth=1)
        plt.axvline(0, color='black', linewidth=1, alpha=0.3)
        
        # Dibujar la raíz si la calculamos
        if metodo != "solo_graficar" and raiz is not None and not np.isnan(raiz):
            plt.plot(r_val, 0, 'ro', markersize=8, label=f'Raíz: {r_val:.4f}')
        
        # Sombrear el intervalo solo si aplica
        if metodo in ['biseccion', 'falsa_posicion']:
            plt.axvspan(p1, p2, color='green', alpha=0.1, label=f'Intervalo [{p1}, {p2}]')

        titulo = f'Gráfica - f(x) = {expr}' if metodo == "solo_graficar" else f'Gráfica - Método: {metodo}'
        plt.title(titulo)
        plt.xlabel('x')
        plt.ylabel('f(x)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.show()
        #plt.savefig('grafica.png') # Descomenta para guardar la gráfica como imagen

if __name__ == "__main__":
    main()