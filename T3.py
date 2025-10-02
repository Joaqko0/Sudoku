import pygame
from typing import Optional, List, Tuple, Set
import random

# ---------------- Configuración de Pygame ----------------
pygame.init()
ANCHO, ALTO = 540, 640  # +100px de HUD inferior
TAM_CASILLA = ANCHO // 9
VENTANA = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("SUDOKU en Pygame - T3") #es el nombre de la ventana

FUENTE = pygame.font.SysFont("arial", 36)
FUENTE_PEQ = pygame.font.SysFont("arial", 20)
FUENTE_MINI = pygame.font.SysFont("arial", 16)

# Paleta de colores
COLOR_BG = (248, 249, 251) #fondo general
COLOR_LINEA = (60, 60, 60)#lineas gruesas que separan los subcuadros
COLOR_LINEA_FINA = (200, 205, 210)#lineas finas que separan las celdas
COLOR_SELECCION = (200, 220, 255)# celda seleccionada
COLOR_HOVER = (0, 100, 255)# celda en hover (mouse encima)
COLOR_IGUALES = (0, 200, 0)# celdas con el mismo valor que la seleccionada
COLOR_SUBCUADRO = (240, 244, 248)# fondo de los subcuadros 3x3
COLOR_FIJA = (20, 20, 20)# numeros fijos del puzzle
COLOR_EDIT = (10, 120, 60)# numeros editables por el usuario
COLOR_ERROR = (210, 0, 0)# borde rojo de celdas con error
COLOR_PIE = (135, 135, 135)# texto en la barra inferior
COLOR_COMPLETO = (150, 150, 150)  # cuando un número ya está completo (9 veces)
COLOR_BADGE = (70, 160, 90) # fondo del badge de números completos

MENSAJES_BONITOS = [
    "¡Qué capo! Una a la vez y lo sacás ",
    "Tu cerebro está on fire ",
    "Respirá… y confía: ¡vos podés! ",
    "Elegante, prolijo y seguro. Seguimos ",
    "¡Hermoso avance! ",
]

Grid = List[List[int]]

# ---------------- Utilidades de Matriz ----------------
def copiar_matriz(m: Grid) -> Grid:
    return [fila[:] for fila in m]

def esta_vacia(m: Grid) -> bool:
    return all(all(v == 0 for v in fila) for fila in m)

#---------------- Lógica de Sudoku (pura, testeable) ----------------
def es_valido(m: Grid, fila: int, col: int, val: int) -> bool:
    if val == 0:
        return True
    # Fila
    if any(m[fila][c] == val for c in range(9) if c != col):
        return False
    # Columna
    if any(m[r][col] == val for r in range(9) if r != fila):
        return False
    # Subcuadro
    sr, sc = (fila // 3) * 3, (col // 3) * 3
    for r in range(sr, sr + 3):
        for c in range(sc, sc + 3):
            if (r, c) != (fila, col) and m[r][c] == val:
                return False
    return True

def tablero_completo(m: Grid) -> bool:
    return all(all(v != 0 for v in fila) for fila in m)

def buscar_vacio(m: Grid) -> Optional[Tuple[int, int]]:
    for r in range(9):
        for c in range(9):
            if m[r][c] == 0:
                return (r, c)
    return None

def resolver_backtracking(m: Grid) -> bool:
    vacio = buscar_vacio(m)
    if not vacio:
        return True
    r, c = vacio
    for val in range(1, 10):
        if es_valido(m, r, c, val):
            m[r][c] = val
            if resolver_backtracking(m):
                return True
            m[r][c] = 0
    return False

def generar_tablero_lleno() -> Grid:
    tablero = [[0] * 9 for _ in range(9)]
    def rellenar():
        vacio = buscar_vacio(tablero)
        if not vacio:
            return True
        r, c = vacio
        numeros = list(range(1, 10))
        random.shuffle(numeros)
        for val in numeros:
            if es_valido(tablero, r, c, val):
                tablero[r][c] = val
                if rellenar():
                    return True
                tablero[r][c] = 0
        return False
    rellenar()
    return tablero

def generar_puzzle(celdas_a_borrar: int = 50) -> Grid:
    tablero = generar_tablero_lleno()
    borradas = 0
    while borradas < celdas_a_borrar:
        r = random.randint(0, 8)
        c = random.randint(0, 8)
        if tablero[r][c] != 0:
            tablero[r][c] = 0
            borradas += 1
    return tablero

# ---------------- Estado del juego ----------------
PUZZLE = generar_puzzle(50)
tablero_inicial: Grid = copiar_matriz(PUZZLE)
tablero: Grid = copiar_matriz(PUZZLE)
celdas_fijas = {(r, c) for r in range(9) for c in range(9) if tablero_inicial[r][c] != 0}
seleccion = (0, 0)
validacion_en_vivo = True  # ON por defecto
mensaje = "Buena suerte bro"
completados: Set[int] = set()  # números que ya aparecen 9 veces
hover: Optional[Tuple[int, int]] = None

# ---------------- Ayudas visuales ----------------
def celdas_con_valor(val: int) -> List[Tuple[int, int]]:
    if val == 0: return []
    return [(r, c) for r in range(9) for c in range(9) if tablero[r][c] == val]

def contar_valor(val: int) -> int:
    return sum(1 for r in range(9) for c in range(9) if tablero[r][c] == val)

def actualizar_completados():
    completados.clear()
    for v in range(1, 10):
        if contar_valor(v) == 9:
            completados.add(v)

def conflicto_detallado(m: Grid, fila: int, col: int, val: int) -> Optional[str]:
    if val == 0: return None
    # fila
    for c in range(9):
        if c != col and m[fila][c] == val:
            return f"Conflicto en FILA {fila+1} con col {c+1}"
    # col
    for r in range(9):
        if r != fila and m[r][col] == val:
            return f"Conflicto en COLUMNA {col+1} con fila {r+1}"
    # sub
    sr, sc = (fila // 3) * 3, (col // 3) * 3
    for r in range(sr, sr + 3):
        for c in range(sc, sc + 3):
            if (r, c) != (fila, col) and m[r][c] == val:
                q = (sr // 3) * 3 + (sc // 3) + 1
                return f"Conflicto en SUBCUADRO {q} (3x3)"
    return None

# ---------------- Dibujo ----------------
def draw_rect_alpha(surface, color, rect):
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    shape_surf.fill(color)
    surface.blit(shape_surf, rect)

def dibujar_grid():
    # fondo general
    VENTANA.fill(COLOR_BG)
    # sombreo suave por subcuadros
    for br in range(3):
        for bc in range(3):
            rect = pygame.Rect(bc*3*TAM_CASILLA, br*3*TAM_CASILLA, 3*TAM_CASILLA, 3*TAM_CASILLA)
            draw_rect_alpha(VENTANA, (*COLOR_SUBCUADRO, 40), rect)

    # líneas del tablero
    for i in range(10):
        grosor = 3 if i % 3 == 0 else 1
        color = COLOR_LINEA if i % 3 == 0 else COLOR_LINEA_FINA
        x = i * TAM_CASILLA
        y = i * TAM_CASILLA
        pygame.draw.line(VENTANA, color, (x, 0), (x, 540), grosor)
        pygame.draw.line(VENTANA, color, (0, y), (540, y), grosor)

def dibujar_resaltados(r_sel: int, c_sel: int):
    # Resalta fila/columna y subcuadro de la selección
    draw_rect_alpha(VENTANA, (*COLOR_HOVER, 70), (0, r_sel*TAM_CASILLA, 540, TAM_CASILLA))
    draw_rect_alpha(VENTANA, (*COLOR_HOVER, 70), (c_sel*TAM_CASILLA, 0, TAM_CASILLA, 540))
    sr, sc = (r_sel//3)*3, (c_sel//3)*3
    draw_rect_alpha(VENTANA, (*COLOR_HOVER, 40), (sc*TAM_CASILLA, sr*TAM_CASILLA, 3*TAM_CASILLA, 3*TAM_CASILLA))

def dibujar_iguales(val: int):
    # Resalta todas las celdas que tengan el mismo valor
    if val == 0: return
    for (r, c) in celdas_con_valor(val):
        draw_rect_alpha(VENTANA, (*COLOR_IGUALES, 90), (c*TAM_CASILLA, r*TAM_CASILLA, TAM_CASILLA, TAM_CASILLA))

def dibujar_hover(hover_cell: Optional[Tuple[int,int]]):
    if not hover_cell: return
    r, c = hover_cell
    draw_rect_alpha(VENTANA, (*COLOR_HOVER, 35), (c*TAM_CASILLA, r*TAM_CASILLA, TAM_CASILLA, TAM_CASILLA))

def dibujar_seleccion(r: int, c: int):
    pygame.draw.rect(VENTANA, COLOR_SELECCION, (c*TAM_CASILLA, r*TAM_CASILLA, TAM_CASILLA, TAM_CASILLA), 0)

def dibujar_numeros():
    for r in range(9):
        for c in range(9):
            val = tablero[r][c]
            if val == 0: continue
            es_fija = (r, c) in celdas_fijas
            color_num = COLOR_FIJA if es_fija else COLOR_EDIT
            if val in completados:
                color_num = COLOR_COMPLETO
            txt = FUENTE.render(str(val), True, color_num)
            cx = c*TAM_CASILLA + TAM_CASILLA//2
            cy = r*TAM_CASILLA + TAM_CASILLA//2
            rect = txt.get_rect(center=(cx, cy))
            VENTANA.blit(txt, rect)

def dibujar_errores():
    if not validacion_en_vivo: return
    for r in range(9):
        for c in range(9):
            if (r, c) in celdas_fijas: continue
            val = tablero[r][c]
            if val == 0: continue
            if not es_valido(tablero, r, c, val):
                rect = pygame.Rect(c*TAM_CASILLA, r*TAM_CASILLA, TAM_CASILLA, TAM_CASILLA)
                pygame.draw.rect(VENTANA, COLOR_ERROR, rect, 3)

def dibujar_pie(texto: str):
    # HUD inferior (100px)
    pygame.draw.rect(VENTANA, (235, 237, 240), (0, 540, ANCHO, 100))
    lbl = FUENTE_PEQ.render(texto, True, COLOR_PIE)
    VENTANA.blit(lbl, (12, 546))
    # Controles
    controls = ""
    VENTANA.blit(FUENTE_MINI.render(controls, True, (70, 70, 70)), (12, 572))
    # Badge números completos
    if completados:
        badge = f"Números completos: {', '.join(map(str, sorted(completados)))}"
        badge_surf = FUENTE_MINI.render(badge, True, (255, 255, 255))
        box = badge_surf.get_rect()
        box.topleft = (12, 596)
        pygame.draw.rect(VENTANA, COLOR_BADGE, (box.x-6, box.y-4, box.w+12, box.h+8), border_radius=10)
        VENTANA.blit(badge_surf, box)

# ---------------- Interacción ----------------
def pos_a_celda(mx: int, my: int) -> Optional[Tuple[int, int]]:
    if 0 <= mx < 540 and 0 <= my < 540:
        return my // TAM_CASILLA, mx // TAM_CASILLA
    return None

def escribir_valor(r: int, c: int, val: int):
    global mensaje
    if (r, c) in celdas_fijas:
        mensaje = "Esa celda es fija del puzzle. Elegí otra."
        return
    if val == 0:
        tablero[r][c] = 0
        actualizar_completados()
        return

    # Escribir y validar
    tablero[r][c] = val
    conflicto = conflicto_detallado(tablero, r, c, val)
    if validacion_en_vivo and conflicto:
        mensaje = f"{conflicto}. Probá otro número."
    else:
        mensaje = random.choice(MENSAJES_BONITOS)
        if tablero_completo(tablero):
            mensaje = " ¡GG! Tablero completo. ¡Crack total!"
    actualizar_completados()

def reiniciar():
    global tablero, mensaje
    tablero = copiar_matriz(tablero_inicial)
    mensaje = "A volver a empezar. Tranqui, ahora sale mejor "
    actualizar_completados()

def resolver():
    global tablero, mensaje
    temp = copiar_matriz(tablero)
    if resolver_backtracking(temp):
        tablero[:] = temp
        mensaje = "Resuelto. Usaste el modo sabio "
    else:
        mensaje = "Este estado no tiene solución. Reintentemos."

# ---------------- Bucle principal ----------------
def main():
    global seleccion, validacion_en_vivo, mensaje, hover
    clock = pygame.time.Clock()
    corriendo = True
    actualizar_completados()

    while corriendo:
        clock.tick(60)
        hover = None

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False

            elif evento.type == pygame.MOUSEMOTION:
                hover = pos_a_celda(*evento.pos)

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif pygame.K_1 <= evento.key <= pygame.K_9:
                    val = evento.key - pygame.K_0
                    r, c = seleccion
                    escribir_valor(r, c, val)
                elif evento.key in (pygame.K_BACKSPACE, pygame.K_0):
                    r, c = seleccion
                    escribir_valor(r, c, 0)
                elif evento.key == pygame.K_v:
                    validacion_en_vivo = not validacion_en_vivo
                    estado = "ON" if validacion_en_vivo else "OFF"
                    mensaje = f"Validación en vivo: {estado}"
                elif evento.key == pygame.K_r:
                    reiniciar()
                elif evento.key == pygame.K_s:
                    resolver()
                elif evento.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    r, c = seleccion
                    if evento.key == pygame.K_UP:    r = (r - 1) % 9
                    if evento.key == pygame.K_DOWN:  r = (r + 1) % 9
                    if evento.key == pygame.K_LEFT:  c = (c - 1) % 9
                    if evento.key == pygame.K_RIGHT: c = (c + 1) % 9
                    seleccion = (r, c)

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                cel = pos_a_celda(*evento.pos)
                if cel:
                    seleccion = cel

        # --- Dibujo de frame ---
        r_sel, c_sel = seleccion
        dibujar_grid()
        dibujar_resaltados(r_sel, c_sel)          # fila/col/subcuadro
        dibujar_hover(hover)                      # celda bajo el mouse
        val_sel = tablero[r_sel][c_sel]
        dibujar_iguales(val_sel)                  # todas las celdas con el mismo número
        dibujar_seleccion(r_sel, c_sel)
        dibujar_numeros()
        dibujar_errores()
        dibujar_pie(mensaje)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
