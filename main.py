import random
import pygame
from pathlib import Path
#? Ruta base del proyecto o ejecutable
BASE_DIR = Path(__file__).resolve().parent
#TODO ---------------------------------------------------------------------------- #
#TODO                             DATOS DEL JUEGO                                #
#TODO ---------------------------------------------------------------------------- #
ANCHO, ALTO = 960, 600
MONSTRUOS = ("Axongor", "Ruppira", "Bryocut")

#! ESTADÍSTICAS
estadisticas = {
    "Axongor": {"vida": 100, "ataque": 80, "defensa": 105, "velocidad": 70},
    "Ruppira": {"vida": 110, "ataque": 115, "defensa": 50, "velocidad": 85},
    "Bryocut": {"vida": 75, "ataque": 120, "defensa": 50, "velocidad": 120},
}

#! MOVIMIENTOS
archivos_ui = {
    "Axongor": ["Regeneración_De_Branquias.png", "Golpe_De_Corrientes.png",
                "Camuflaje_Pantanoso.png", "Escudo_Acuático.png"],
    "Ruppira": ["Latido_De_Gema.png", "Espejismo.png",
                "Golpe_Veloz.png", "Explosion_Ignea.png"],
    "Bryocut": ["Ráfaga_De_Cortes.png", "Corte_Preciso.png",
                "Estatua_Engañosa.png", "Camuflaje_Floral.png"],
}
ataques_dano = {"Axongor": (1,), "Ruppira": (2, 3), "Bryocut": (0, 1)}
prioridades = {"Axongor": {3: 2}, "Ruppira": {2: 1}, "Bryocut": {}}
movimientos_evasion = {"Axongor": 2, "Ruppira": 1, "Bryocut": 3}

#TODO ---------------------------------------------------------------------------- #
#TODO                                   FUNCIONES                                  #
#TODO ---------------------------------------------------------------------------- #
def cargar_imagen(ruta, tamano, transparente=True, suave=False):
    """Carga y escala una imagen una única vez."""
    imagen = pygame.image.load(str(BASE_DIR / ruta))
    imagen = imagen.convert_alpha() if transparente else imagen.convert()
    escala = pygame.transform.smoothscale if suave else pygame.transform.scale
    return escala(imagen, tamano)


def obtener_estadisticas(nombre):
    return estadisticas[nombre].copy()


def dibujar_barra_vida(superficie, x, y, vida, vida_max):
    #* Barra de vida
    ancho, alto = 240, 18
    largo = int(ancho * vida / vida_max)
    pygame.draw.rect(superficie, (70, 70, 70), (x, y, ancho, alto)) #gris
    pygame.draw.rect(superficie, (0, 255, 0), (x, y, largo, alto)) #verde
    pygame.draw.rect(superficie, (0, 0, 0), (x, y, ancho, alto), 2) #negro

def dibujar_panel_vida(superficie, rect, nombre, datos, vida_max, fuente):
    # Fondo beige
    pygame.draw.rect(superficie, (245, 240, 220), rect, border_radius=18)
    pygame.draw.rect(superficie, (120, 110, 90), rect, 2, border_radius=18)

    # Textos
    superficie.blit(fuente.render(nombre, True, (0, 0, 0)), (rect.x + 15, rect.y + 15))
    superficie.blit(fuente.render(f"HP: {datos['vida']}", True, (0, 0, 0)), (rect.x + 15, rect.y + 50))

    # Barra de vida
    dibujar_barra_vida(superficie, rect.x + 15, rect.y + 85, datos["vida"], vida_max)

def determinar_primero(nombre_j, ataque_j, nombre_r, ataque_r):
    #* Primero prioridad del movimiento, después velocidad y al final azar
    jugador = (prioridades[nombre_j].get(ataque_j, 0), estadisticas[nombre_j]["velocidad"])
    rival = (prioridades[nombre_r].get(ataque_r, 0), estadisticas[nombre_r]["velocidad"])
    return random.choice((True, False)) if jugador == rival else jugador > rival #Devuelve True si jugador primero o Falso si rival primero

def elegir_movimiento_rival(nombre, datos):
    #* Evitar curaciones inútiles y no repetir buffs todavía activos
    bloqueados = set()

    if nombre == "Axongor" and datos["vida"] >= estadisticas["Axongor"]["vida"]:
        bloqueados.add(0)  # Regeneración de Branquias

    if nombre == "Ruppira" and datos.get("cargas_gema", 0) > 0:
        bloqueados.add(0)  # Latido de Gema

    if nombre == "Bryocut" and datos.get("estatua", False):
        bloqueados.add(2)  # Estatua Engañosa

    if datos.get("cargas_evasion", 0) > 0:
        bloqueados.add(movimientos_evasion[nombre])

    if nombre == "Axongor" and datos.get("escudo", False):
        bloqueados.add(3)

    disponibles = [i for i in range(len(archivos_ui[nombre])) if i not in bloqueados]
    return random.choice(disponibles)

def ejecutar_movimiento(nombre, indice, atacante, defensor):
    movimiento = archivos_ui[nombre][indice].removesuffix(".png").replace("_", " ")

    #! COMPROBACIONES DE BUFFS
    #* Curación de Axongor
    if nombre == "Axongor" and indice == 0:
        antes = atacante["vida"]
        atacante["vida"] = min(estadisticas[nombre]["vida"], antes + 30)
        return f"{nombre} usó {movimiento}: +{atacante['vida'] - antes} HP"

    #* Latido de Gema de Ruppira: +30% durante 2 ataques acertados
    if nombre == "Ruppira" and indice == 0:
        atacante["cargas_gema"] = 2
        return "Ruppira usó Latido de Gema (+30%, 2 ataques)"

    #* Evasión de los tres monstruos
    if indice == movimientos_evasion[nombre]:
        atacante["cargas_evasion"] = 2
        return f"{nombre} usó {movimiento}: evasión activada"

    #* Escudo Acuático: prioridad +2 y dura solo este turno
    if nombre == "Axongor" and indice == 3:
        atacante["escudo"] = True
        return "Axongor activó Escudo Acuático"

    #* Estatua Engañosa: duplica el próximo ataque acertado
    if nombre == "Bryocut" and indice == 2:
        atacante["estatua"] = True
        return "Bryocut usó Estatua Engañosa: próximo ataque x2"

    #! MOVIMIENTOS OFENSIVOS
    if indice not in ataques_dano[nombre]:
        return f"{nombre} usó {movimiento} (sin efecto aún)"

    #* Comprobar escudo antes de aplicar cualquier efecto
    if defensor.get("escudo", False):
        defensor["escudo"] = False
        return f"Escudo Acuático bloqueó {movimiento} de {nombre}"

    #* Evasión: cada ataque entrante consume una carga
    if defensor.get("cargas_evasion", 0) > 0:
        defensor["cargas_evasion"] -= 1
        if random.random() < 0.35:
            return f"{nombre} usó {movimiento}, ¡pero falló!"

    #* Cálculo del daño y bonificaciones (solo si el ataque acertó)
    dano = max(1, round(atacante["ataque"] * 15 / (defensor["defensa"] + 50)))
    if atacante.get("cargas_gema", 0) > 0:
        dano = round(dano * 1.3)
        atacante["cargas_gema"] -= 1

    potenciado = nombre == "Bryocut" and atacante.get("estatua", False)
    if potenciado:
        dano = round(dano * 2)
        atacante["estatua"] = False

    #* Ráfaga de Cortes: entre 2 y 5 golpes al 40% del daño
    if nombre == "Bryocut" and indice == 0:
        por_golpe = max(1, round(dano * 0.4))
        vida_anterior = defensor["vida"]
        golpes_dados = 0
        for _ in range(random.randint(2, 5)):
            if defensor["vida"] == 0:
                break
            defensor["vida"] = max(0, defensor["vida"] - por_golpe)
            golpes_dados += 1
        extra = " ¡POTENCIADO!" if potenciado else ""
        return f"Ráfaga de Cortes: {golpes_dados} golpes, -{vida_anterior - defensor['vida']} HP{extra}"

    #* Corte Preciso: 40% de probabilidad de crítico x1.5
    critico = nombre == "Bryocut" and indice == 1 and random.random() < 0.40
    if critico:
        dano = round(dano * 1.5)

    #* Restar HP y construir el mensaje
    defensor["vida"] = max(0, defensor["vida"] - dano)
    mensaje = f"{nombre} usó {movimiento}: -{dano} HP"
    if critico:
        mensaje += " ¡CRÍTICO!"
    if potenciado:
        mensaje += " ¡POTENCIADO!"

    #* Explosión Ígnea: 30% de quemar durante 3 finales de turno
    if nombre == "Ruppira" and indice == 3 and defensor["vida"] > 0:
        if random.random() < 0.30:
            defensor["quemado"] = 3
            mensaje += " ¡QUEMADURA!"
    return mensaje

def seleccion_fondo():
    fondos_disponibles = ['Torneo','Desierto_Carmesi','Jardín_Esmeralda', 'Santuario_Cristalino','Zona_Entrenamiento']
    eleccion_fondo = random.randint(0,4)
    return cargar_imagen("assets/escenarios/" + fondos_disponibles[eleccion_fondo] + '.png', (ANCHO, ALTO), False)
   
#TODO ---------------------------------------------------------------------------- #
#TODO                           INICIO Y CARGA DEL JUEGO                          #
#TODO ---------------------------------------------------------------------------- #
def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))  # TAMAÑO
    pygame.display.set_caption("CopiMon")              # TÍTULO
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 28)
    fuente_mensajes = pygame.font.SysFont(None, 22)
    #? Temporizador para la pantalla de resultados
    momento_resultado = 0
    #? PANELES DE VIDA
    panel_rival = pygame.Rect(15, 20, 320, 120)
    panel_jugador = pygame.Rect(630, 310, 320, 120)
    #? FONDOS
    fondo= seleccion_fondo()
    ruta_menu = "assets/ui/Menu/"
    fondos = {
        nombre: cargar_imagen(ruta_menu + f"Fondo_{nombre}.png", (ANCHO, ALTO), False)
        for nombre in ("Menu", "Seleccion", "Victoria", "Derrota", "Empate")
    }

    #? BOTONES DE MENÚ Y SELECCIÓN
    jugar = cargar_imagen(ruta_menu + "Jugar.png", (340, 90), suave=True)
    salir = cargar_imagen(ruta_menu + "Salir.png", (340, 90), suave=True)
    seleccionar = cargar_imagen(ruta_menu + "Seleccionar.png", (240, 80), suave=True)
    menu = cargar_imagen(ruta_menu + "Menu.png", (180, 50), suave=True)
    menu_resultado = cargar_imagen(ruta_menu + "Menu.png", (350, 100), suave=True)
    rect_jugar = jugar.get_rect(center=(480, 330))
    rect_salir = salir.get_rect(center=(480, 435))
    rect_menu = menu.get_rect(midtop=(ANCHO // 2, 10))
    rect_menu_resultado = menu_resultado.get_rect(center=(ANCHO // 2, 450))
    rect_seleccionar = [seleccionar.get_rect(center=(x, 465)) for x in (215, 480, 745)]

    #? SPRITES Y BOTONES DE ATAQUE: precargados para evitar lecturas en cada partida
    sprites_jugador = {
        n: cargar_imagen(f"assets/sprites/{n.lower()}_espalda.png", (360, 360))
        for n in MONSTRUOS
    }
    sprites_rival = {
        n: cargar_imagen(f"assets/sprites/{n.lower()}_frente.png", (300, 300))
        for n in MONSTRUOS
    }
    botones_ataque = {
        n: [cargar_imagen("assets/ui/" + archivo, (245, 100), suave=True)
            for archivo in archivos_ui[n]]
        for n in MONSTRUOS
    }
    rect_jugador = sprites_jugador["Axongor"].get_rect(midbottom=(285, 540))
    rect_rival = sprites_rival["Ruppira"].get_rect(midbottom=(690, 340))

    #? ÁREAS DE CLIC DE ATAQUES:
    ancho_boton, alto_boton, separacion_x, margen = 225, 80, 10, 15
    inicio_x = ANCHO - 2 * ancho_boton - separacion_x - margen
    inicio_y = ALTO - 2 * alto_boton - margen
    rect_botones = [
        pygame.Rect(inicio_x + (i % 2) * (ancho_boton + separacion_x),
                    inicio_y + (i // 2) * alto_boton, ancho_boton, alto_boton)
        for i in range(4)
    ]

    #? ESTADO DE LA PARTIDA
    jugando, estado_juego = True, "menu"
    nombre_jugador, nombre_rival = "Axongor", "Ruppira"  # CASO BASE
    datos_jugador = obtener_estadisticas(nombre_jugador)
    datos_rival = obtener_estadisticas(nombre_rival)
    mensajes_turno = ["¡Selecciona un movimiento!"]
    acciones_pendientes = []
    proximo_ataque = 0
    resultado = None

    #TODO ---------------------------------------------------------------------------- #
    #TODO                                     JUEGO                                    #
    #TODO ---------------------------------------------------------------------------- #
    
    while jugando:
        #? EVENTOS DEL MENÚ, SELECCIÓN, RESULTADOS Y COMBATE
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jugando = False  # CONDICIÓN DE PARADA
                break
            if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
                continue

            if estado_juego == "menu":
                fondo= seleccion_fondo()
                if rect_jugar.collidepoint(evento.pos):
                    estado_juego = "seleccion"
                elif rect_salir.collidepoint(evento.pos):
                    jugando = False

            elif estado_juego == "seleccion":
                for i, rect in enumerate(rect_seleccionar):
                    if not rect.collidepoint(evento.pos):
                        continue 
                    #* Elegir monstruo y rival aleatorio diferente
                    nombre_jugador = MONSTRUOS[i]
                    nombre_rival = random.choice([n for n in MONSTRUOS if n != nombre_jugador])
                    datos_jugador = obtener_estadisticas(nombre_jugador)
                    datos_rival = obtener_estadisticas(nombre_rival)
                    mensajes_turno = ["¡Selecciona un movimiento!"]
                    acciones_pendientes.clear()
                    resultado = None
                    estado_juego = "combate"
                    break

            elif estado_juego == "resultado":
                if rect_menu_resultado.collidepoint(evento.pos):
                    estado_juego = "menu"

            elif estado_juego == "combate":
                #* Regresar al menú y cancelar las acciones restantes
                if rect_menu.collidepoint(evento.pos):
                    estado_juego = "menu"
                    acciones_pendientes.clear()
                elif not acciones_pendientes and datos_jugador["vida"] > 0 and datos_rival["vida"] > 0:
                    for i, rect in enumerate(rect_botones):
                        if rect.collidepoint(evento.pos):
                            #* Crear acciones y ordenarlas por prioridad / velocidad
                            ataque_rival = elegir_movimiento_rival(nombre_rival, datos_rival)
                            accion_j = (nombre_jugador, i, datos_jugador, datos_rival)
                            accion_r = (nombre_rival, ataque_rival, datos_rival, datos_jugador)
                            primero = determinar_primero(nombre_jugador, i, nombre_rival, ataque_rival)
                            acciones_pendientes = [accion_j, accion_r] if primero else [accion_r, accion_j]
                            mensajes_turno = []
                            proximo_ataque = pygame.time.get_ticks()
                            break

        if not jugando:
            break

        #? Esperar 2 segundos antes de mostrar la pantalla de resultado
        if estado_juego == "esperando_resultado" and pygame.time.get_ticks() - momento_resultado >= 2000:
            estado_juego = "resultado"

        #? ACCIONES PENDIENTES: una acción cada 700 ms
        if estado_juego == "combate" and acciones_pendientes and pygame.time.get_ticks() >= proximo_ataque:
            nombre, indice, atacante, defensor = acciones_pendientes.pop(0)
            if atacante["vida"] > 0 and defensor["vida"] > 0:
                mensajes_turno.append(ejecutar_movimiento(nombre, indice, atacante, defensor))
            proximo_ataque = pygame.time.get_ticks() + 700

            #* Cancelar el resto del turno si alguien fue derrotado
            if datos_jugador["vida"] == 0 or datos_rival["vida"] == 0:
                acciones_pendientes.clear()

            if not acciones_pendientes:
                #* Quemaduras: 5 HP durante tres finales de turno (sin HP negativos)
                if datos_jugador["vida"] > 0 and datos_rival["vida"] > 0:
                    for nombre, datos in ((nombre_jugador, datos_jugador), (nombre_rival, datos_rival)):
                        if datos.get("quemado", 0) > 0:
                            dano = min(5, datos["vida"])
                            datos["vida"] -= dano
                            datos["quemado"] -= 1
                            mensajes_turno.append(f"{nombre} pierde {dano} HP por quemadura")

                #* Desactivar escudos al terminar el turno (aunque no recibieran ataques)
                datos_jugador["escudo"] = datos_rival["escudo"] = False

                #* Determinar resultado: victoria, derrota o empate
                if datos_jugador["vida"] == 0 and datos_rival["vida"] == 0:
                    resultado = "Empate"
                elif datos_rival["vida"] == 0:
                    resultado = "Victoria"
                elif datos_jugador["vida"] == 0:
                    resultado = "Derrota"
                if resultado:
                    estado_juego = "esperando_resultado"
                    momento_resultado = pygame.time.get_ticks()
                    acciones_pendientes.clear()

        #! DIBUJADO DE PANTALLAS
        if estado_juego == "menu":
            #* Fondo y botones del menú principal
            pantalla.blit(fondos["Menu"], (0, 0))
            pantalla.blit(jugar, rect_jugar)
            pantalla.blit(salir, rect_salir)

        elif estado_juego == "seleccion":
            #* Fondo con tres tarjetas y botones de selección
            pantalla.blit(fondos["Seleccion"], (0, 0))
            for rect in rect_seleccionar:
                pantalla.blit(seleccionar, rect)

        elif estado_juego == "resultado":
            #* Fondo de Victoria, Derrota o Empate y botón para volver al menú
            pantalla.blit(fondos[resultado], (0, 0))
            pantalla.blit(menu_resultado, rect_menu_resultado)

        elif estado_juego in ("combate", "esperando_resultado"):
            #* Fondo y personajes
            pantalla.blit(fondo, (0, 0))
            pantalla.blit(sprites_jugador[nombre_jugador], rect_jugador)
            pantalla.blit(sprites_rival[nombre_rival], rect_rival)

            #* Paneles de vida
            dibujar_panel_vida(
                pantalla,
                panel_rival,
                nombre_rival,
                datos_rival,
                estadisticas[nombre_rival]["vida"],
                fuente
            )

            dibujar_panel_vida(
                pantalla,
                panel_jugador,
                nombre_jugador,
                datos_jugador,
                estadisticas[nombre_jugador]["vida"],
                fuente
            )

            #* Panel inferior del combate
            color_panel = (12, 75, 90)  # Cian oscuro
            pygame.draw.rect(pantalla, color_panel, (0, 435, ANCHO, 165))
            #* Botones de movimientos: imagen 245x100, área clicable 225x80
            for imagen, rect in zip(botones_ataque[nombre_jugador], rect_botones):
                pantalla.blit(imagen, rect)

            #* Cuadro y mensajes de los dos últimos acontecimientos
            pygame.draw.rect(pantalla, (245, 245, 235), (15, 455, 460, 110), border_radius=8)
            for i, mensaje in enumerate(mensajes_turno[-2:]):
                pantalla.blit(fuente_mensajes.render(mensaje, True, (0, 0, 0)), (25, 475 + i * 27))

            #* Botón para regresar al menú durante el combate
            pantalla.blit(menu, rect_menu)

        #* Actualización de pantalla y límite de FPS, una sola vez por ciclo
        pygame.display.flip()
        reloj.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()
