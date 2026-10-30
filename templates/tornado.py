"""Tornado procedural mediante sistemas de particulas (Blender 4.2.x).

Responsabilidades de este modulo (plantilla):
    * Crear y configurar UN tornado: emisor, sistema de particulas,
      campos de fuerza y material.
    * NO orquestar la escena completa (camara, luces, rango de frames,
      bakes, etc.): eso pertenece a ``composition/``.

Reutilizacion de global_utils (no se duplica funcionalidad):
    * ``emitter_particles.set_emitter`` : crea el aro emisor base
      (circulo Bezier extruido convertido a malla).
    * ``particles.Particle``            : instancia del sistema de
      particulas (count/tipo/pasos de pelo) y sus force fields.
    * ``material.Material``             : creacion/asignacion de
      materiales con la nomenclatura y nodos del proyecto.

Convenciones del proyecto respetadas:
    * Mismo mecanismo de imports que ``main.py``: raiz del proyecto en
      ``sys.path`` + ``importlib.reload`` para desarrollo iterativo
      dentro de Blender (addon "Run Script").
    * Nombres descriptivos, validaciones explicitas y mensajes claros.
"""

import importlib
import math
import sys
from pathlib import Path

import bpy

# Raiz del proyecto (templates/ esta un nivel por debajo de main.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from global_utils import emitter_particles, particles
from materials import material as material_module

# Recarga desde disco (convencion de main.py)
importlib.reload(emitter_particles)
importlib.reload(particles)
importlib.reload(material_module)


class Tornado:
    """Una instancia de tornado procedural con particulas de pelo.

    La forma de embudo se consigue emitiendo desde un aro cuyo radio es
    el radio inferior del tornado: las particulas suben con velocidad
    inicial proporcional a la altura, mientras un campo VORTEX las hace
    girar alrededor del eje vertical y un campo WIND ascendente las
    estira hacia arriba. Con ``top_radius < bottom_radius`` (y el
    termino ``-t^2`` del perfil radial) la silueta resultante es mas
    ancha abajo/media y mas estrecha arriba.

    Parameters
    ----------
    name : str
                Nombre base del objeto/material ("Tornado_01", ...).
    height : float
                Altura de la columna de aire (unidades de escena).
    bottom_radius : float
                Radio del aro emisor (parte baja del embudo).
    top_radius : float
                Radio objetivo en la parte alta; controla el grosor del
                cuello superior del embudo.
    particle_count : int
                Numero total de hebras de pelo emitidas.
    particle_lifetime : float
                Vida util de cada particula en fotogramas.
    emission_start : int
                Primer frame del sistema de particulas.
    emission_end : int
                Ultimo frame de emision.
    rotation_speed : float
                Velocidad angular del vortice (radianes/fotograma aprox.).
    upward_speed : float
                Velocidad ascendente de las particulas (unidades/frame).
    seed : float
                Semilla aleatoria para resultados reproducibles.
    location : tuple
                Posicion de la base del tornado en la escena.
    node_spacing : int | None
                Espaciado de nodos del material (usa el default de la
                clase Material si es None).
    """

    # ------------------------------------------------------------------ #
    # Valores por defecto de la plantilla (parametricos, no hardcodeados)
    # ------------------------------------------------------------------ #
    DEFAULTS = {
        "height": 8.0,
        "bottom_radius": 1.5,
        "top_radius": 0.5,
        "particle_count": 6000,
        "particle_lifetime": 100.0,
        "emission_start": 1,
        "emission_end": 80,
        "rotation_speed": 1.2,
        "upward_speed": 0.35,
        "seed": 0.0,
        "location": (0.0, 0.0, 0.0),
        # Material (nomenclatura del proyecto: *_Material)
        "math_operation": "ADD",
        "emission_strength": 0.05,
        "emission_color": (0.75, 0.75, 0.78, 1.0),
        "ramp_interpolation": material_module.Material.DEFAULT_RAMP_INTERP,
        "ramp_position": material_module.Material.DEFAULT_RAMP_POS,
    }

    def __init__(
        self,
        name: str = "Tornado",
        *,
        height: float = DEFAULTS["height"],
        bottom_radius: float = DEFAULTS["bottom_radius"],
        top_radius: float = DEFAULTS["top_radius"],
        particle_count: int = DEFAULTS["particle_count"],
        particle_lifetime: float = DEFAULTS["particle_lifetime"],
        emission_start: int = DEFAULTS["emission_start"],
        emission_end: int = DEFAULTS["emission_end"],
        rotation_speed: float = DEFAULTS["rotation_speed"],
        upward_speed: float = DEFAULTS["upward_speed"],
        seed: float = DEFAULTS["seed"],
        location: tuple = DEFAULTS["location"],
        node_spacing: int | None = None,
        math_operation: str = DEFAULTS["math_operation"],
        emission_strength: float = DEFAULTS["emission_strength"],
        emission_color: tuple = DEFAULTS["emission_color"],
    ):
        self.name = self._validate_name(name)
        self.height = self._positive("height", height)
        self.bottom_radius = self._positive("bottom_radius", bottom_radius)
        self.top_radius = self._positive("top_radius", top_radius)
        self.particle_count = self._positive_int("particle_count", particle_count)
        self.particle_lifetime = self._positive("particle_lifetime", particle_lifetime)
        self.seed = self._non_negative_float("seed", seed)
        self.rotation_speed = float(rotation_speed)
        self.upward_speed = float(upward_speed)
        self.location = tuple(location)
        self.node_spacing = node_spacing

        # Parametros del material (se consumen en _build_material)
        self.math_operation = str(math_operation)
        self.emission_strength = self._non_negative_float(
            "emission_strength", emission_strength)
        if (not isinstance(emission_color, (tuple, list))
                or len(emission_color) != 4):
            raise ValueError(
                "'emission_color' debe ser un RGBA de 4 componentes "
                f"(recibido: {emission_color!r})")
        self.emission_color = tuple(float(c) for c in emission_color)

        start, end = self._validate_frames(emission_start, emission_end)
        self.emission_start = start
        self.emission_end = end

        # Referencias que se llenan al construir
        self.emitter_obj = None       # objeto emisor (aro convertido a malla)
        self.emitter_partsys = None   # Particle("EMITTER"): dinamica del vortice
        self.partsys = None           # Particle("HAIR"): hebras visibles
        self.modifier = None          # ParticleSystemModifier del emisor
        self.material = None          # instancia materials.Material
        self.force_fields = []        # objetos effector creados

        self.build()

    # ------------------------------------------------------------------ #
    # Validaciones
    # ------------------------------------------------------------------ #
    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Nombre de tornado invalido: {name!r}")
        return name.strip()

    @staticmethod
    def _positive(label: str, value) -> float:
        value = float(value)
        if value <= 0.0:
            raise ValueError(f"'{label}' debe ser > 0 (recibido: {value})")
        return value

    @staticmethod
    def _non_negative_float(label: str, value) -> float:
        value = float(value)
        if value < 0.0:
            raise ValueError(f"'{label}' no puede ser negativo (recibido: {value})")
        return value

    @staticmethod
    def _positive_int(label: str, value) -> int:
        value = int(value)
        if value <= 0:
            raise ValueError(f"'{label}' debe ser un entero > 0 (recibido: {value})")
        return value

    @staticmethod
    def _validate_frames(start, end) -> tuple[int, int]:
        start, end = int(start), int(end)
        if start < 0:
            raise ValueError(f"'emission_start' no puede ser negativo ({start})")
        if end <= start:
            raise ValueError(
                f"'emission_end' ({end}) debe ser mayor que 'emission_start' ({start})"
            )
        return start, end

    # ------------------------------------------------------------------ #
    # Perfil del embudo (funnel)
    # ------------------------------------------------------------------ #
    def radius_at(self, t: float) -> float:
        """Radio del embudo en la fraccion de altura ``t`` (0=base, 1=top).

        Interpolacion lineal bottom->top mas un termino cuadratico de
        abombamiento que ensancha la zona media/baja y afila la parte
        superior (silueta clasica de tornado).
        """
        t = min(max(float(t), 0.0), 1.0)
        linear = self.bottom_radius + (self.top_radius - self.bottom_radius) * t
        bulge = max(self.bottom_radius - self.top_radius, 0.0) * 0.5
        return max(linear - bulge * t * t, 0.01)

    # ------------------------------------------------------------------ #
    # Construccion
    # ------------------------------------------------------------------ #
    def build(self):
        """Monta emisor + particulas + fuerzas + material (idempotente)."""
        self._build_emitter()
        self._build_particles()
        self._build_force_fields()
        self._build_material()

    # --- Emisor ---------------------------------------------------------
    def _build_emitter(self):
        """Crea el aro emisor reutilizando ``emitter_particles.set_emitter``.

        El helper del proyecto genera un circulo Bezier extruido y lo
        convierte a malla; aqui se posiciona/reescala segun el perfil del
        embudo y se le da una ligera inclinacion para romper la simetria
        perfecta del vortice.
        """
        tilt = math.radians(5.0)
        emitter_particles.set_emitter(
            radius=1.0,                       # escala unitaria; se ajusta abajo
            rotation=(tilt, math.radians(90), tilt),
            bevel=self.bottom_radius * 0.02,  # grosor minimo visible
            extrude=self.bottom_radius * 0.05,
            render=False,
        )
        obj = bpy.context.active_object
        obj.name = f"{self.name}_Emitter"
        # El helper rota el aro 90 deg en Y (plano vertical); se gira -90
        # en X para devolverlo al plano XY (horizontal) manteniendo el tilt.
        obj.rotation_euler[0] += math.radians(-90)
        obj.location = (
            self.location[0],
            self.location[1],
            self.location[2] + self.radius_at(0.05),  # base ligeramente elevada
        )
        scale_mid = self.radius_at(0.4)
        obj.scale = (scale_mid, scale_mid, scale_mid)
        bpy.ops.object.transform_apply(rotation=True, scale=True)
        self.emitter_obj = obj

    # --- Sistema de particulas ------------------------------------------
    def _build_particles(self):
        """Configura el sistema de particulas reutilizando ``particles.Particle``.

        El objeto aro es un EMISOR de tipo "EMITTER": la clase ``Particle``
        valida el tipo y configura la emision dinamica (ventana de frames,
        vida util, distribucion). Las hebras visuales del embudo se
        construyen encima con un segundo sistema "HAIR" (el pelo no puede
        emitirse desde un sistema EMITTER; Blender exige un unico tipo por
        sistema), por lo que el tornado queda 100% hecho por particulas.
        """
        bpy.ops.object.select_all(action="DESELECT")
        self.emitter_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.emitter_obj

        # --- Capa EMITTER: dinamica base del vortice ----------------------
        # Particulas con fisica newtoniana emitidas durante la ventana
        # emission_start..emission_end; son las que los campos VORTEX/WIND
        # arrastran en espiral ascendente.
        self.emitter_partsys = particles.Particle(
            "EMITTER",
            self.particle_count,
            name=f"{self.name}_EmitterParticles",
            frame_start=self.emission_start,
            frame_end=self.emission_end,
            lifetime=self.particle_lifetime,
            physics_type="NEWTONIAN",
            life_random=min(0.3, (self.seed % 1.0) * 0.3),
        )
        # Bifurcacion EMITTER de is_particle: aplica ventana de emision,
        # vida util, distribucion y dinamica pasando los kwargs propios
        # del emisor (velocidad normal al aro proporcional a
        # upward_speed + variacion aleatoria para romper la simetria).
        self.emitter_partsys.is_particle(
            emit_from="FACE",
            normal_factor=1.0 + self.upward_speed * 10.0,
            factor_random=0.15,
            brownian_factor=0.02 + (self.seed % 5) * 0.01,
            effect_factor=1.0,
            mass=0.02,
            size=max(self.bottom_radius * 0.02, 0.01),
        )
        eps = self.emitter_partsys.partsys
        eps.use_advanced_hair = True
        eps.time_offset = int(self.seed) % 1000
        # Las particulas EMITTER no se renderizan como puntos: aportan la
        # dinamica; el aspecto visual lo dan las hebras HAIR de abajo.
        eps.use_render_emitter = False

        # --- Capa HAIR: hebras visibles del embudo ------------------------
        self.partsys = particles.Particle("HAIR", self.particle_count)
        ps = self.partsys.partsys
        ps.name = f"{self.name}_ParticleSettings"

        # Pasos de pelo: largo = relacion altura/radio, pasos finos para
        # curvas suaves del vortice.
        hair_length = self.height / max(self.bottom_radius, 0.01)
        self.partsys.is_particle(hair_length=hair_length, hair_step=8,
                                 display_step=4, render_step=2)

        # --- Emision temporizada ----------------------------------------
        ps.frame_start = self.emission_start
        ps.frame_end = self.emission_end
        # Que el ciclo de vida cubra toda la ventana de emision+ascenso.
        ps.lifetime = round(self.particle_lifetime)
        ps.life_random = min(0.3, (self.seed % 1.0) * 0.3)

        # --- Distribucion sobre el aro -----------------------------------
        ps.distribution = "RAND"
        ps.use_advanced_hair = True   # habilita normal_factor/factor_random
        # Emisor es una malla con caras (aro Bezier extruido+bevel), por lo
        # que "FACE" es un enum valido para emit_from en Blender 4.2.
        ps.emit_from = "FACE"

        # --- Movimiento ascendente inicial -------------------------------
        ps.effector_weights.gravity = 0.0
        # Velocidad normal al emisor proporcional a upward_speed, con
        # ligera variacion aleatoria para romper la simetria del anillo.
        ps.normal_factor = 1.0 + self.upward_speed * 10.0
        ps.factor_random = 0.15

        # --- Semilla reproducible -----------------------------------------
        # El "Random" de las particulas (usado por el nodo HairInfo del
        # material y por los pasos de pelo) es derivable del seed: se
        # desplaza la fase temporal del sistema en ``seed`` frames, de
        # modo que dos tornados con seeds distintos generan patrones
        # distintos y el mismo seed reproduce siempre el mismo patron.
        ps.time_offset = int(self.seed) % 1000

        self.modifier = next((m for m in self.emitter_obj.modifiers
                              if m.type == "PARTICLE_SYSTEM"), None)

    # --- Campos de fuerza -------------------------------------------------
    def _build_force_fields(self):
        """Vortex (rotacion) + Wind ascendente via ``Particle.set_force_field``.

        Las magnitudes se derivan de los parametros del tornado:
            vortex.strength ~ rotation_speed * height / bottom_radius
            wind.strength   ~ upward_speed * 100
        """
        mid_z = self.location[2] + self.height * 0.5
        vortex_strength = abs(self.rotation_speed) * self.height / self.bottom_radius
        self.partsys.set_force_field(
            "VORTEX",
            location=(self.location[0], self.location[1], mid_z),
            strength=vortex_strength,
        )
        vortex_obj = bpy.context.object
        vortex_obj.name = f"{self.name}_Vortex"
        vortex_obj.field.falloff_type = "INVERSE_SQUARE"
        vortex_obj.field.flow = 0.5           # componente radial de succión
        vortex_obj.field.noise = 0.3 + (self.seed % 10.0) * 0.05

        wind_strength = self.upward_speed * 100.0
        self.partsys.set_force_field(
            "WIND",
            location=(self.location[0], self.location[1], self.location[2]),
            strength=wind_strength,
        )
        wind_obj = bpy.context.object
        wind_obj.name = f"{self.name}_Wind"
        # La luz/effector WIND sopla a lo largo de su eje -Z local:
        # rotando X 90 deg el flujo queda dirigido hacia +Z (arriba).
        wind_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
        wind_obj.field.noise = 0.2
        wind_obj.field.frequency = 0.4

        self.force_fields = [vortex_obj, wind_obj]

    # --- Material -----------------------------------------------------------
    def _build_material(self):
        """Crea y asigna el material usando la clase Material del proyecto.

        Respeta la nomenclatura ``<Nombre>_Material`` y reutiliza
        ``set_hair_nodes`` (HairInfo -> ColorRamp -> Math -> Emission),
        que es justo el grafo adecuado para hebras de pelo del tornado.
        La logica de materiales queda aislada del resto de la plantilla.
        """
        mat_name = f"{self.name}_Material"
        self.material = material_module.Material(
            mat_name,
            node_spacing=self.node_spacing
            or material_module.Material.DEFAULT_NODE_SPACING,
        )
        self.material.set_hair_nodes(
            self.math_operation,
            self.emission_strength,
            self.emission_color,
            ramp_interpolation=self.DEFAULTS["ramp_interpolation"],
            ramp_position=self.DEFAULTS["ramp_position"],
        )
        self.assign_to([self.emitter_obj])

    # ------------------------------------------------------------------ #
    # API publica
    # ------------------------------------------------------------------ #
    def assign_to(self, objects: list):
        """Asigna el material del tornado a una lista de objetos."""
        if self.material is None:
            raise RuntimeError("El material aun no fue creado; llama build() primero.")
        for obj in objects:
            obj.data.materials.clear()
            obj.data.materials.append(self.material.material)

    def set_keyframes(self):
        """Animacion basica del vortice: giro lento del propio emisor.

        Solo toca objetos de ESTE tornado; la animacion de escena
        (rango de frames, bakes) la decide ``composition/``.
        """
        spin_turns = self.rotation_speed / 10.0
        start_rot = tuple(self.emitter_obj.rotation_euler)
        self.emitter_obj.rotation_euler = start_rot
        self.emitter_obj.keyframe_insert("rotation_euler", frame=self.emission_start)
        end_rot = list(start_rot)
        end_rot[2] += math.radians(360.0 * spin_turns)
        self.emitter_obj.rotation_euler = end_rot
        self.emitter_obj.keyframe_insert("rotation_euler", frame=self.emission_end)
        if self.emitter_obj.animation_data and self.emitter_obj.animation_data.action:
            for fc in self.emitter_obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        # Devuelve el objeto a su pose inicial (el keyframe del primer
        # frame ya guarda el valor correcto).
        self.emitter_obj.rotation_euler = start_rot

    def to_dict(self) -> dict:
        """Resumen de configuracion (utiles para logs/composiciones)."""
        return {
            "name": self.name,
            "height": self.height,
            "bottom_radius": self.bottom_radius,
            "top_radius": self.top_radius,
            "particle_count": self.particle_count,
            "particle_lifetime": self.particle_lifetime,
            "emission_start": self.emission_start,
            "emission_end": self.emission_end,
            "rotation_speed": self.rotation_speed,
            "upward_speed": self.upward_speed,
            "seed": self.seed,
            "location": self.location,
            "particle_types": ["EMITTER", "HAIR"],
        }

    def remove(self, purge: bool = False):
        """Elimina de la escena SOLO los objetos de este tornado.

        Nunca toca objetos ajenos. Con ``purge=True`` tambien borra los
        data-blocks huerfanos (material/particulas) asociados.
        """
        targets = [self.emitter_obj] + list(self.force_fields)
        for obj in targets:
            if obj and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        if purge:
            if self.material and self.material.material in bpy.data.materials:
                bpy.data.materials.remove(self.material.material)
            for partsys in (self.partsys, self.emitter_partsys):
                if partsys and partsys.partsys in bpy.data.particles:
                    bpy.data.particles.remove(partsys.partsys)
        self.emitter_obj = None
        self.emitter_partsys = None
        self.partsys = None
        self.modifier = None
        self.material = None
        self.force_fields = []

    def __repr__(self) -> str:
        return (f"<Tornado {self.name!r} h={self.height:.1f} "
                f"r=({self.bottom_radius:.2f}->{self.top_radius:.2f}) "
                f"n={self.particle_count}>")


# Alias de modulo: "clase Tornado.py" -> crear instancias simples.
def create_tornado(**kwargs) -> Tornado:
    """Factory funcional: ``create_tornado(height=10, ...)``."""
    return Tornado(**kwargs)
