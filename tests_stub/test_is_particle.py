"""Prueba de la bifurcacion EMITTER en Particle.is_particle (usa stub bpy)."""
import sys

sys.path.insert(0, "/workspace/tests_stub")   # stub bpy
sys.path.insert(0, "/workspace")

import bpy  # noqa: E402
from global_utils.particles import Particle  # noqa: E402


def new_obj(name):
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.view_layer.objects.active
    o.name = name
    return o


# ---------------------------------------------------------------- HAIR
o = new_obj("HairObj")
h = Particle("HAIR", 500)
h.is_particle(2, 6, 6, 6)                      # firma posicional historica
assert h.partsys.type == "HAIR"
assert h.partsys.hair_length == 2.0 and h.partsys.hair_step == 6
assert h.partsys.display_step == 6 and h.partsys.render_step == 6
print("OK  HAIR: bifurcacion pelo conserva comportamiento historico")

# ------------------------------------------------- EMITTER sin kwargs
e = Particle("EMITTER", 1200, name="Tornado_EmitterParticles",
             frame_start=10, frame_end=200, lifetime=90, life_random=0.25,
             physics_type="NEWTONIAN")
e.is_particle()                                # nueva bifurcacion EMITTER
ps = e.partsys
assert ps.type == "EMITTER" and ps.count == 1200
assert ps.name == "Tornado_EmitterParticles"
assert ps.physics_type == "NEWTONIAN"
assert ps.frame_start == 10 and ps.frame_end == 200
assert ps.lifetime == 90 and abs(ps.life_random - 0.25) < 1e-6
assert ps.distribution == "RAND" and ps.use_rotations is True
assert ps.normal_factor == 1.0                 # default parametrico
print("OK  EMITTER: is_particle() configura emision/vida/fisica")

# ------------------------------------- EMITTER con kwargs escalables
m = Particle("EMITTER", 800, lifetime=60, emitter_type="OBJECT")
m.is_particle(emit_from="FACE",
              normal_factor=3.5, factor_random=0.15, brownian_factor=0.04,
              effect_factor=1.0, damping=0.03, mass=0.02, size=0.07,
              size_random=0.4)
mps = m.partsys
assert mps.emit_from == "FACE"
assert mps.normal_factor == 3.5 and mps.factor_random == 0.15
assert mps.brownian_factor == 0.04 and mps.mass == 0.02
assert mps.particle_size == 0.07 and mps.size_random == 0.4
assert mps.effector_weights.gravity == 0.0
assert mps.render_type == "OBJECT" and mps.use_render_emitter is False
print("OK  EMITTER: kwargs delegados a set_emitter_motion + render_type")

# -------------------------------------------------- argumentos invalidos
try:
    Particle("EMITTER", 10).is_particle(emit_from="CORNERS")
    raise AssertionError("debia rechazar emit_from invalido")
except ValueError as ex:
    print(f"OK  EMITTER: rechaza emit_from invalido -> {ex}")

# HAIR debe IGNORAR los kwargs de emisor (misma firma para ambos tipos)
i = Particle("HAIR", 100)
i.is_particle(hair_length=4, emit_from="FACE", normal_factor=9.0)
assert i.partsys.hair_length == 4.0
assert "normal_factor" not in i.partsys.__dict__
print("OK  HAIR: ignora kwargs de EMITTER sin romper nada")

# Tipos no soportados siguen rechazandose
for bad in ("CLOUD", "", 42, None):
    try:
        Particle(bad, 10)
        raise AssertionError(f"debia rechazar tipo {bad!r}")
    except (ValueError, TypeError):
        pass
print("OK  validacion de tipo intacta")

print("\nTODAS LAS PRUEBAS DE is_particle (HAIR + EMITTER) PASARON")
