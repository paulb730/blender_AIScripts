import bpy


class Particle:
    """Configura un sistema de particulas sobre el objeto activo.

    Tipos soportados (enum ``type`` de ParticleSettings en Blender 4.2):
        * "EMITTER" : particulas de malla/objeto con dinamica de cuerpo
          completo o newborn (emision continua en el tiempo).
        * "HAIR"    : hebras de pelo (estaticas o con dinámica capilar).

    Parameters
    ----------
    tipo : str
        Tipo de sistema de particulas; debe ser "EMITTER" o "HAIR".
    count : int
        Numero de particulas emitidas.
    name : str | None
        Nombre del data-block ParticleSettings; si es None se conserva el
        nombre autogenerado por Blender.
    frame_start / frame_end : int
        Ventana de emision (solo tiene efecto en sistemas EMITTER; se
        guardan igualmente para HAIR estatico no afectan al aspecto).
    lifetime / life_random : float
        Vida util de cada particula en fotogramas y variacion aleatoria.
    physics_type : str | None
        Para EMITTER: "NEWTONIAN" (cuerpo completo clasico) o "NEWBORN"
        (sin integracion: las particulas quedan donde nacen, util para
        distribuir objetos sobre una superficie). Si es None se mantiene
        el valor por defecto de Blender ("NEWTONIAN").
    emitter_type : str | None
        Para EMITTER: renderizado de las particulas, "PARTICLE" (punto),
        "OBJECT" (instancea ``instance_object``) o "COLLECTION".
    """

    VALID_TYPES = ("EMITTER", "HAIR")
    VALID_PHYSICS = ("NEWTONIAN", "NEWBORN", "FIELD")

    def __init__(self, tipo, count, *, name: str | None = None,
                 frame_start: int = 1, frame_end: int = 100,
                 lifetime: float = 100.0, life_random: float = 0.0,
                 physics_type: str | None = None,
                 emitter_type: str | None = None):
        self.tipo = self._validate_type(tipo)
        self.count = self._validate_count(count)
        self.name = name
        self.frame_start = int(frame_start)
        self.frame_end = int(frame_end)
        self.lifetime = float(lifetime)
        self.life_random = float(life_random)
        self.physics_type = self._validate_physics(physics_type)
        self.emitter_type = self._validate_emitter_type(emitter_type)
        # El sistema se anade al objeto ACTIVO; si el caller ya tiene un
        # emisor seleccionado, debe poder reutilizarlo (convencion del
        # proyecto: main.py y templates/tornado.py seleccionan el emisor
        # antes de instanciar la clase). Si no hay ninguno, se crea un
        # plano minimo para no romper usos sueltos.
        if bpy.context.view_layer.objects.active is None:
            bpy.ops.mesh.primitive_plane_add(size=0.01)
        bpy.ops.object.particle_system_add()
        # Se captura el settings del sistema recien anadido (ultimo
        # modificador de particulas del activo): robusto incluso cuando
        # el objeto ya tenia sistemas previos (multi-capa EMITTER+HAIR).
        active = bpy.context.view_layer.objects.active
        modifiers = [m for m in active.modifiers if m.type == "PARTICLE_SYSTEM"]
        self.partsys = modifiers[-1].settings

    # ------------------------------------------------------------------ #
    # Validaciones
    # ------------------------------------------------------------------ #
    @staticmethod
    def _validate_type(tipo) -> str:
        if not isinstance(tipo, str):
            raise TypeError(
                f"'tipo' debe ser una cadena ({'|'.join(Particle.VALID_TYPES)}), "
                f"recibido: {tipo!r}")
        tipo_norm = tipo.strip().upper()
        if tipo_norm not in Particle.VALID_TYPES:
            raise ValueError(
                f"Tipo de particula invalido: {tipo!r}. "
                f"Tipos aceptados: {', '.join(Particle.VALID_TYPES)}")
        return tipo_norm

    @staticmethod
    def _validate_count(count) -> int:
        count = int(count)
        if count <= 0:
            raise ValueError(f"'count' debe ser un entero > 0 (recibido: {count})")
        return count

    @staticmethod
    def _validate_physics(physics_type):
        if physics_type is None:
            return None
        physics_norm = str(physics_type).strip().upper()
        if physics_norm not in Particle.VALID_PHYSICS:
            raise ValueError(
                f"physics_type invalido: {physics_type!r}. "
                f"Aceptados: {', '.join(Particle.VALID_PHYSICS)}")
        return physics_norm

    @staticmethod
    def _validate_emitter_type(emitter_type):
        if emitter_type is None:
            return None
        emitter_norm = str(emitter_type).strip().upper()
        if emitter_norm not in ("PARTICLE", "OBJECT", "COLLECTION"):
            raise ValueError(
                f"emitter_type invalido: {emitter_type!r}. "
                f"Aceptados: PARTICLE, OBJECT, COLLECTION")
        return emitter_norm

    # ------------------------------------------------------------------ #
    # Configuracion base
    # ------------------------------------------------------------------ #
    def set_particlesystem(self):
        """Aplica tipo y cantidad al data-block de particulas."""
        self.partsys.type = self.tipo
        self.partsys.count = self.count

    def is_particle(self,
                    hair_length: float = 2.0,
                    hair_step: int = 6,
                    display_step: int = 6,
                    render_step: int = 6,
                    *,
                    emit_from: str | None = None,
                    use_rotations: bool = True,
                    **emitter_kwargs):
        """Bifurca la configuracion segun el tipo de particula.

        Nuevas bifurcaciones (``self.tipo``):
          * "HAIR"    -> ``_configure_hair(...)``: largo de hebra y pasos
            de interpolacion (comportamiento historico de la funcion).
          * "EMITTER" -> ``_configure_emitter(...)``: ventana de emision,
            vida util, distribucion y dinamica del emisor. Acepta kwargs
            extra escalables (``normal_factor``, ``factor_random``,
            ``brownian_factor``, ``effect_factor``, ``damping``, ``mass``,
            ``size``, ``size_random``) que se delegan en
            ``set_emitter_motion``.

        Los argumentos de pelo se ignoran para sistemas EMITTER y los
        kwargs de emisor se ignoran para sistemas HAIR, de modo que la
        misma firma funciona para ambos tipos (retrocompatible con las
        llamadas posicionales ya existentes, p.ej. ``is_particle(2,6,6,6)``).
        """
        self.set_particlesystem()
        if self.name:
            self.partsys.name = self.name

        if self.tipo == "HAIR":
            self._configure_hair(hair_length, hair_step,
                                 display_step, render_step)
        elif self.tipo == "EMITTER":
            self._configure_emitter(emit_from=emit_from,
                                    use_rotations=use_rotations,
                                    **emitter_kwargs)
        else:  # pragma: no cover - VALID_TYPES evita llegar aqui
            raise ValueError(
                f"Tipo sin bifurcacion en is_particle: {self.tipo!r}")

    # ------------------------------------------------------------------ #
    # Logica especifica por tipo (bifurcaciones de is_particle)
    # ------------------------------------------------------------------ #
    def _configure_hair(self, hair_length: float, hair_step: int,
                        display_step: int, render_step: int):
        """Bifurcacion HAIR: largo de hebra y pasos de interpolacion."""
        ps = self.partsys
        ps.hair_length = float(hair_length)
        ps.hair_step = int(hair_step)
        ps.display_step = int(display_step)
        ps.render_step = int(render_step)

    def _configure_emitter(self, *, emit_from: str | None = None,
                           use_rotations: bool = True, **emitter_kwargs):
        """Bifurcacion EMITTER: deja el sistema como emisor dinamico.

        Configura fisica, frames de emision y vida util, y aplica la
        dinamica de emision via ``set_emitter_motion`` usando los kwargs
        recibidos (o los valores por defecto parametricos).
        """
        ps = self.partsys
        ps.physics_type = self.physics_type or "NEWTONIAN"
        ps.frame_start = self.frame_start
        ps.frame_end = self.frame_end
        ps.lifetime = max(1, round(self.lifetime))
        ps.life_random = max(0.0, float(self.life_random))
        ps.count = self.count
        ps.distribution = "RAND"
        ps.use_rotations = bool(use_rotations)
        if emit_from is not None:
            emit_from = str(emit_from).strip().upper()
            if emit_from not in ("VERT", "EDGE", "FACE", "VOLUME"):
                raise ValueError(
                    f"emit_from invalido: {emit_from!r}. "
                    "Aceptados: VERT, EDGE, FACE, VOLUME")
            ps.emit_from = emit_from
        # Dinamica de emision (escalable): kwargs -> set_emitter_motion.
        self.set_emitter_motion(**emitter_kwargs)
        if self.emitter_type is not None:
            ps.render_type = self.emitter_type
            ps.use_render_emitter = False

    def set_emitter_motion(self, *, normal_factor: float = 1.0,
                           factor_random: float = 0.0,
                           brownian_factor: float = 0.0,
                           effect_factor: float = 1.0,
                           damping: float = 4.0e-2,
                           mass: float = 0.01,
                           size: float = 0.05,
                           size_random: float = 0.5):
        """Ajusta la dinamica de un sistema EMITTER (velocidad, tamano...).

        Solo aplica si ``self.tipo == "EMITTER"``; lanza RuntimeError para
        evitar configurar un sistema de pelo con parametros inexistentes.
        """
        if self.tipo != "EMITTER":
            raise RuntimeError(
                "set_emitter_motion solo es valido para sistemas 'EMITTER' "
                f"(tipo actual: {self.tipo!r})")
        ps = self.partsys
        ps.normal_factor = float(normal_factor)
        ps.factor_random = float(factor_random)
        ps.brownian_factor = float(brownian_factor)
        ps.effector_weights.gravity = 0.0
        ps.effector_weights.all = float(effect_factor)
        ps.damp = float(damping)
        ps.mass = float(mass)
        ps.particle_size = float(size)
        ps.size_random = float(size_random)

    def set_instance_object(self, obj):
        """Instancea un objeto/collection en cada particula (EMITTER)."""
        if self.tipo != "EMITTER":
            raise RuntimeError(
                "set_instance_object solo es valido para sistemas 'EMITTER' "
                f"(tipo actual: {self.tipo!r})")
        ps = self.partsys
        if isinstance(obj, bpy.types.Collection):
            ps.instance_collection = obj
            ps.render_type = "COLLECTION"
            ps.use_collection_instances = True
        else:
            ps.instance_object = obj
            ps.render_type = "OBJECT"
        ps.use_render_emitter = False

    # ------------------------------------------------------------------ #
    # Campos de fuerza
    # ------------------------------------------------------------------ #
    def set_force_field(self, force_tipo, location: tuple = (0, 0, 1.26),
                        strength: float = 25):
        """Anade un effector (VORTEX, WIND, TURBULENCE...) a la escena."""
        bpy.ops.object.effector_add(type=force_tipo, location=location)
        bpy.context.object.field.strength = strength
