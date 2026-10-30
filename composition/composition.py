"""Composicion de escenas con tornados (orquestacion de animacion).

Responsabilidades de este modulo:
    1. Importar la plantilla desde ``templates/tornado.py``.
    2. Crear uno o varios tornados con una configuracion dada.
    3. Definir el rango de fotogramas de la escena segun los tornados.
    4. Configurar la animacion/parametros temporales (keyframes, playback).
    5. Organizar objetos y materiales dentro de una Coleccion propia.
    6. Desencadenar la simulacion/reproduccion de particulas (frame_set).
    7. Quedar abierto a otros elementos/efectos via ``extra_builders``.

La logica DEL tornado vive en templates/tornado.py; aqui solo se coordina.
"""

import importlib
import sys
from pathlib import Path

import bpy

# Mismo mecanismo de imports que main.py (raiz del proyecto en sys.path)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from global_utils import helpers
from templates import tornado as tornado_module
from templates import tornado_presets

importlib.reload(helpers)
importlib.reload(tornado_module)
importlib.reload(tornado_presets)


class TornadoComposition:
    """Composicion que agrupa tornados y orquesta su animacion."""

    COLLECTION_NAME = "Tornado_Composition"

    def __init__(self, name: str = "TornadoScene", *, clean_scene: bool = False):
        if not name.strip():
            raise ValueError("El nombre de la composicion no puede estar vacio")
        self.name = name.strip()
        self.tornadoes: list[tornado_module.Tornado] = []
        if clean_scene:
            helpers.clean_scene()

    # ------------------------------------------------------------------ #
    # Construccion de tornados
    # ------------------------------------------------------------------ #
    def add_tornado(self, tipo: str | None = None, *, name: str | None = None,
                    **overrides) -> tornado_module.Tornado:
        """Instancia un tornado (opcionalmente desde un preset de tipo).

        Los nombres se derivan de ``self.name`` + indice para evitar
        colisiones entre instancias dentro de la misma composicion.
        """
        idx = len(self.tornadoes) + 1
        tname = name or f"{self.name}_Tornado_{idx:02d}"
        kwargs = tornado_presets.get(tipo) if tipo else {}
        kwargs.update(overrides)
        try:
            obj = tornado_module.Tornado(name=tname, **kwargs)
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                f"No se pudo crear el tornado {tname!r} (tipo={tipo!r}): {exc}"
            ) from exc
        self.tornadoes.append(obj)
        print(f"[composition] tornado creado: {obj!r}")
        return obj

    def build_all(self, specs: list[dict]):
        """Crea varios tornados de golpe desde una lista de especificaciones.

        Cada spec es un dict con claves opcionales: ``type``, ``name`` y
        cualquier override de ``Tornado`` (height, location, seed, ...).
        """
        for spec in specs:
            spec = dict(spec)
            self.add_tornado(spec.pop("type", None),
                             name=spec.pop("name", None), **spec)
        return self.tornadoes

    # ------------------------------------------------------------------ #
    # Organizacion de la escena
    # ------------------------------------------------------------------ #
    def _get_or_create_collection(self) -> bpy.types.Collection:
        """Coleccion propia; reutilizable sin duplicados (idempotente)."""
        coll = bpy.data.collections.get(self.COLLECTION_NAME)
        if coll is None:
            coll = bpy.data.collections.new(self.COLLECTION_NAME)
            bpy.context.scene.collection.children.link(coll)
        return coll

    def organize(self):
        """Mueve TODOS los objetos de esta composicion a su coleccion.

        Solo toca objetos creados por sus tornados; nunca mueve ajenos.
        """
        coll = self._get_or_create_collection()
        for t in self.tornadoes:
            objs = [t.emitter_obj] + list(t.force_fields)
            for obj in objs:
                if obj is None or obj.name not in bpy.data.objects:
                    continue
                for user_coll in list(obj.users_collection):
                    user_coll.objects.unlink(obj)
                if obj.name not in coll.objects:
                    coll.objects.link(obj)

    # ------------------------------------------------------------------ #
    # Animacion / tiempo
    # ------------------------------------------------------------------ #
    def frame_range(self) -> tuple[int, int]:
        """Rango [start, end] cubriendo emision+vida de todos los tornados."""
        if not self.tornadoes:
            raise RuntimeError("No hay tornados en la composicion; "
                               "llama add_tornado/build_all primero.")
        start = min(t.emission_start for t in self.tornadoes)
        end = max(int(t.emission_end + t.particle_lifetime)
                  for t in self.tornadoes)
        return start, end

    def setup_animation(self, fps: int = 24):
        """Define rango de frames, fps y keyframes de cada tornado."""
        scene = bpy.context.scene
        start, end = self.frame_range()
        scene.frame_start = start
        scene.frame_end = end
        scene.render.fps = fps
        for t in self.tornadoes:
            t.set_keyframes()
        return start, end

    def run_simulation(self, step: int = 10):
        """Ejecuta la simulacion de particulas recorriendo los frames.

        En Blender la simulacion se calcula al avanzar el tiempo; aquí se
        avanza el playhead por tramos (``step`` frames) para poblar la
        cache sin bloquear el render completo.
        """
        scene = bpy.context.scene
        start, end = self.frame_range()
        for frame in range(start, end + 1, step):
            scene.frame_set(frame)
        scene.frame_set(start)
        print(f"[composition] simulacion recorrida: frames {start}..{end}")

    # ------------------------------------------------------------------ #
    # Extension: otros elementos/efectos de la composicion
    # ------------------------------------------------------------------ #
    def add_extra(self, builder_callable):
        """Registra un builder externo (p.ej. nubes, escombros, luces).

        ``builder_callable(composicion)`` se ejecuta tras organizar; el
        resultado NO se gestiona automaticamente (responsabilidad del
        efecto externo), pero puede anadirse a la coleccion si lo desea.
        """
        if not callable(builder_callable):
            raise TypeError("add_extra espera un callable(composicion)")
        return builder_callable(self)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def remove(self, purge: bool = True):
        """Elimina SOLO los tornados de esta composicion y su coleccion."""
        for t in self.tornadoes:
            t.remove(purge=purge)
        self.tornadoes.clear()
        coll = bpy.data.collections.get(self.COLLECTION_NAME)
        if coll and not coll.objects and not coll.children:
            bpy.data.collections.remove(coll)


# ---------------------------------------------------------------------- #
# Composicion de ejemplo: dos tornados de tipos distintos
# ---------------------------------------------------------------------- #
def compose_demo() -> TornadoComposition:
    """Composicion basica reutilizable desde main.py u otros scripts."""
    comp = TornadoComposition(name="Demo_Tornados")
    comp.build_all([
        {"type": "funnel", "location": (0.0, 0.0, 0.0)},
        {"type": "rope", "location": (6.0, -2.0, 0.0), "seed": 42},
    ])
    comp.organize()
    start, end = comp.setup_animation(fps=24)
    comp.run_simulation(step=10)
    print(f"[composition] demo lista: frames {start}..{end}, "
          f"{len(comp.tornadoes)} tornados")
    return comp


if __name__ == "__main__":
    compose_demo()
