"""Servidor WebSocket para conectar Flutter y Unity al mismo tiempo."""

import asyncio
import itertools
import json
import random
import sys
import threading
import time
from pathlib import Path

import websockets

_DIR_BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR_BACKEND / "logicaJuego"))
sys.path.insert(0, str(_DIR_BACKEND))

from juego import Juego
import partida


PUERTO = 8000
NUMERO_NOCHE_INICIAL = 1
NUMERO_NOCHE_FINAL = 6

INTERVALO_PING_SEGUNDOS = 20
TIMEOUT_PING_SEGUNDOS = 20

DURACION_POR_TIPO = {
    "cables": 30,
    "dials": 20,
    "sequence": 25,
    "rhythm": 15,
    "wifi": 15,
    "temperatura": 20,
    "ventiladores": 20,
    "procesar_datos": 15,
    "subir_datos": 12,
    "trazar_curso": 20,
}

DESCRIPCION_POR_TIPO = {
    "cables": "Conectar los cables del color correcto",
    "dials": "Girar perillas a posición correcta",
    "sequence": "Resolver la secuencia mostrada",
    "rhythm": "Seguir el ritmo crítico",
    "wifi": "Reiniciar WiFi",
    "temperatura": "Reparar temperatura",
    "ventiladores": "Reparar ventiladores",
    "procesar_datos": "Procesar datos",
    "subir_datos": "Subir datos",
    "trazar_curso": "Trazar curso",
}

TAREA_TIPO_GENERICO_INICIAL = "cables"

_contador_task_id = itertools.count(1)


class ServidorJuego:
    def __init__(self):
        self.clienteTablet = None
        self.clientes = set()
        self.loopAsyncio = None
        self.juego = None
        self.hiloJuego = None
        self.playerIdActivo = None
        self.tareasActivas = {}

    def alEventoDeJuego(self, tipo, datos):
        if tipo == "nueva_tarea_pendiente":
            self.crearTarea(datos["task_type"])

        if tipo == "tarea_cancelada":
            self.cancelarTareaActivaPorTipo(datos["task_type"])

        if (
            tipo == "game_over"
            and self.playerIdActivo is not None
            and self.juego is not None
        ):
            if self.juego.jugadorMurio:
                noche = self.juego.numeroNoche
            elif self.juego.numeroNoche >= NUMERO_NOCHE_FINAL:
                noche = NUMERO_NOCHE_INICIAL
                datos["result"] = "final_victory"
                print("¡Juego completado! Reiniciando progreso desde la noche 1.")
            else:
                noche = self.juego.numeroNoche + 1

            partida.guardarUltimaNoche(self.playerIdActivo, noche)
            print(
                f"Progreso guardado: player_id={self.playerIdActivo} "
                f"próxima_noche={noche}"
            )

        self._enviarAlCliente(datos)

    def _enviarAlCliente(self, datos):
        if self.loopAsyncio is None:
            return

        mensaje = json.dumps(datos)

        asyncio.run_coroutine_threadsafe(
            self._enviarATodos(mensaje),
            self.loopAsyncio,
        )

    async def _enviarATodos(self, mensaje):
        clientes = list(self.clientes)

        if not clientes:
            return

        resultados = await asyncio.gather(
            *(cliente.send(mensaje) for cliente in clientes),
            return_exceptions=True,
        )

        for cliente, resultado in zip(clientes, resultados):
            if isinstance(resultado, Exception):
                self.clientes.discard(cliente)

    def crearTaskParams(self, tipo, numeroNoche):
        if tipo != "dials":
            return {}

        numDiales = 3 if numeroNoche >= 4 else 2
        tolerancia = 10 if numeroNoche >= 4 else 15
        targets = [random.randint(0, 11) * 30 for _ in range(numDiales)]

        return {
            "num_dials": numDiales,
            "targets": targets,
            "tolerance": tolerancia,
        }

    def crearTarea(self, tipo):
        taskId = next(_contador_task_id)
        numeroNoche = self.juego.numeroNoche if self.juego else 1

        mensaje = {
            "task_id": taskId,
            "task_type": tipo,
            "duration": DURACION_POR_TIPO[tipo],
            "description": DESCRIPCION_POR_TIPO[tipo],
            "difficulty": numeroNoche,
            "timestamp": int(time.time() * 1000),
            "task_params": self.crearTaskParams(tipo, numeroNoche),
        }

        self.tareasActivas[taskId] = mensaje
        self.enviarListaDeTareas()

    def cancelarTareaActivaPorTipo(self, tipo):
        idsACancelar = [
            taskId
            for taskId, tarea in self.tareasActivas.items()
            if tarea["task_type"] == tipo
        ]

        for taskId in idsACancelar:
            del self.tareasActivas[taskId]
            print(
                f"Tarea cancelada: task_id={taskId} tipo={tipo}"
            )

        if idsACancelar:
            self.enviarListaDeTareas()

    def enviarListaDeTareas(self):
        self._enviarAlCliente(
            {
                "type": "task_list",
                "tasks": list(self.tareasActivas.values()),
                "timestamp": int(time.time() * 1000),
            }
        )

    def manejarMensajeDeTablet(self, mensaje):
        tipo = mensaje.get("type")

        if tipo == "connect":
            playerId = mensaje.get("player_id")
            print(f"Tablet conectada: player_id={playerId}")

            if self.juego is not None:
                self.juego.juego = False

            if self.hiloJuego is not None:
                self.hiloJuego.join()

            self.playerIdActivo = playerId
            self.juego = None
            self.hiloJuego = None
            self.tareasActivas = {}

            modo = mensaje.get("modo", "nuevo")

            if modo == "continuar":
                numeroNoche = (
                    partida.obtenerUltimaNoche(playerId)
                    or NUMERO_NOCHE_INICIAL
                )
                print(f"Continuar: retomando en noche {numeroNoche}.")
            else:
                numeroNoche = NUMERO_NOCHE_INICIAL
                partida.guardarUltimaNoche(playerId, numeroNoche)
                print("Nuevo juego: empezando desde la noche 1.")

            self.iniciarJuego(numeroNoche)

        elif tipo == "task_completed":
            self._finalizarTarea(mensaje, exito=True)

        elif tipo == "task_failed":
            self._finalizarTarea(mensaje, exito=False)

        elif tipo == "dar_cuerda_inicio":
            if self.juego is not None:
                self.juego.iniciarDarCuerda()
            print("Jugador empezó a dar cuerda a Puppet.")

        elif tipo == "dar_cuerda_fin":
            if self.juego is not None:
                self.juego.detenerDarCuerda()
            print("Jugador dejó de dar cuerda a Puppet.")

        elif tipo == "disconnect":
            print(
                f"Tablet se desconectó: "
                f"razon={mensaje.get('reason')}"
            )

    def _finalizarTarea(self, mensaje, exito):
        taskId = mensaje.get("task_id")
        tareaOriginal = self.tareasActivas.pop(taskId, None)

        if self.juego is not None:
            if exito:
                self.juego.registrarTareaCompletada()
            else:
                self.juego.registrarTareaFallida()

            if tareaOriginal is not None:
                self.juego.resolverTarea(tareaOriginal["task_type"])

        estado = "completada" if exito else "fallida"
        print(f"Tarea {estado}: task_id={taskId}")

        if not self.tareasActivas and self.juego is not None:
            self.crearTarea(TAREA_TIPO_GENERICO_INICIAL)
        else:
            self.enviarListaDeTareas()

    def iniciarJuego(self, numeroNoche):
        if self.juego is not None:
            return

        self.juego = Juego(
            numeroNoche=numeroNoche,
            alEventoDeJuego=self.alEventoDeJuego,
        )

        self.hiloJuego = threading.Thread(
            target=self.juego.iniciar,
            daemon=True,
        )

        self.hiloJuego.start()
        self.crearTarea(TAREA_TIPO_GENERICO_INICIAL)


servidorJuego = ServidorJuego()


async def manejarConexion(websocket):
    servidorJuego.loopAsyncio = asyncio.get_running_loop()
    servidorJuego.clientes.add(websocket)

    print("Cliente conectado.")

    try:
        async for mensajeCrudo in websocket:
            mensaje = json.loads(mensajeCrudo)
            tipo = mensaje.get("type")

            if tipo == "unity_connect":
                print("Unity conectado.")
                continue

            if tipo == "connect":
                servidorJuego.clienteTablet = websocket

            servidorJuego.manejarMensajeDeTablet(mensaje)

    except websockets.exceptions.ConnectionClosed:
        print("Cliente desconectado.")

    finally:
        servidorJuego.clientes.discard(websocket)

        if servidorJuego.clienteTablet is websocket:
            servidorJuego.clienteTablet = None


async def main():
    async with websockets.serve(
        manejarConexion,
        "0.0.0.0",
        PUERTO,
        ping_interval=INTERVALO_PING_SEGUNDOS,
        ping_timeout=TIMEOUT_PING_SEGUNDOS,
    ):
        print(
            f"Servidor escuchando en ws://0.0.0.0:{PUERTO}"
        )

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())