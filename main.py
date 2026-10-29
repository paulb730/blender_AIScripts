
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


def setup_materials():
    hair_material=material.Material("Hair_Material")
    hair_material.set_hair_nodes("MULTIPLY", 25, (1.0, 0.0, 0.0, 1.0))
    

def main():
    helpers.clean_scene()
    environment_setup()
    particle_setup()
    setup_materials()


main()




