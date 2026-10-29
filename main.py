
from pathlib import Path
import sys
import importlib

# Ruta absoluta del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent
# Verificar que global_utils exista junto a main.py
UTILS_PATH = PROJECT_ROOT / "global_utils"
MATS_PATH = PROJECT_ROOT / "materials"
# Agregar la raíz del proyecto a las rutas de importación
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if not UTILS_PATH.is_dir() or not MATS_PATH.is_dir():
    raise FileNotFoundError(
        f"No se encontró global_utils o materials en: {UTILS_PATH}, {MATS_PATH}"
    )    


from global_utils import emitter_particles, helpers,lighting, particles
from materials import material
importlib.reload(helpers)
importlib.reload(emitter_particles)
importlib.reload(particles)
importlib.reload(lighting)
importlib.reload(material)
import math


def environment_setup():
        helpers.create_backdrop(26,
                            (5, 0, 0),
                            (0, math.radians(-90), 0))
        lighting.set_lighting(100,
                             (0, 0, 5),"AREA")
        helpers.set_scene([1080,1080],128
                    ,"GPU","CYCLES",(0.0,0.0,0.0,1))

        helpers.set_camera((-11.0,0,0),
                       (math.radians(90),
                        0,
                        math.radians(-90)),70)
#emitter_particles.set_emitter(1.0,(0,math.radians(90),0),0.01,0.02,False)

def particle_setup():
     emitter_particles.set_emitter(1.0,(0,math.radians(90),0),0.01,0.02,False)
     hair_particles=particles.Particle("HAIR",8000)
     hair_particles.is_particle(2,6,6,6)

     hair_particles.set_force_field("TURBULENCE", (0, 0, 1.20), 25)


# ---------------------------------------------------------------------------
# Parametros de los materiales (nada hardcodeado dentro de las funciones)
# ---------------------------------------------------------------------------
MATERIALS_CONFIG = {
    "hair": {
        "name": "Hair_Material",
        "node_spacing": material.Material.DEFAULT_NODE_SPACING,
        "math_operation": "MULTIPLY",
        "emission_strength": 25,
        "emission_color": (1.0, 0.0, 0.0, 1.0),
        "ramp_interpolation": material.Material.DEFAULT_RAMP_INTERP,
        "ramp_position": material.Material.DEFAULT_RAMP_POS,
    },
}


def build_hair_material(cfg: dict) -> material.Material:
    """Instancia un Material de pelo a partir de un diccionario de config."""
    hair_material = material.Material(
        cfg["name"],
        node_spacing=cfg["node_spacing"],
    )
    hair_material.set_hair_nodes(
        cfg["math_operation"],
        cfg["emission_strength"],
        cfg["emission_color"],
        ramp_interpolation=cfg["ramp_interpolation"],
        ramp_position=cfg["ramp_position"],
    )
    return hair_material


def setup_materials(config: dict | None = None):
    """Crea todos los materiales definidos en la configuracion dada.

    Si no se pasa ninguna configuracion se usa MATERIALS_CONFIG, de modo que
    agregar un material nuevo solo requiere anadir una entrada al diccionario.
    """
    config = config if config is not None else MATERIALS_CONFIG

    builders = {"hair": build_hair_material}

    materials = {}
    for key, cfg in config.items():
        builder = builders.get(key)
        if builder is None:
            raise KeyError(f"No existe builder para el material '{key}'")
        materials[key] = builder(cfg)

    return materials


def main():
    helpers.clean_scene()
    environment_setup()
    particle_setup()
    setup_materials()


main()




