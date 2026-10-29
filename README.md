# BPYDINOSAUR 🦖

Proyecto de **automatización de escenas en Blender** mediante scripts Python (API `bpy`). Incluye dos flujos de trabajo:

1. **Escena procedural de partículas / pelo (main.py)** — configuración modular de entorno, emisores, sistemas de partículas y materiales.
2. **BPYDINOSAUR.py** — generador procedural de un modelo tipo *T-Rex* para vista previa de estudio en Cycles (Blender 4.x).

## Estructura del proyecto

```
.
├── main.py                  # Punto de entrada: monta la escena de partículas
├── BPYDINOSAUR.py           # Script independiente: T-Rex procedural de estudio
├── testt.py                 # Prueba/experimento suelto (backdrop, luz, emisor)
├── global_utils/            # Utilidades reutilizables
│   ├── helpers.py           #   clean_scene, set_scene, set_camera, create_backdrop
│   ├── lighting.py          #   set_lighting (luces AREA/otros tipos)
│   ├── emitter_particles.py #   set_emitter (emisor a partir de círculo Bézier)
│   └── particles.py         #   Clase Particle (HAIR, force fields, pasos de render)
└── materials/
    └── material.py          # Clase Material (nodos de pelo: Hair Info, Color Ramp, Emission)
```

## Requisitos

- **Blender 4.x** (los scripts usan la API `bpy`, no se ejecutan con Python externo)
- GPU recomendada para render en Cycles (configurable a CPU)

## Uso

### Escena de partículas (`main.py`)

1. Abrir **Blender 4.x** → workspace **Scripting**.
2. Abrir y ejecutar `main.py` (*Run Script*). Debe estar junto a las carpetas `global_utils/` y `materials/`.
3. El script:
   - Limpia la escena (`helpers.clean_scene`).
   - Crea el fondo/backdrop, una luz de área y la cámara; ajusta resolución (1080×1080), 128 muestras y motor **CYCLES**.
   - Genera un emisor (círculo Bézier convertido a malla) con **8000 partículas de pelo** y un campo de fuerza **TURBULENCE**.
   - Crea el material `Hair_Material` con nodos de pelo (emisión roja multiplicada ×25).
4. Ver en modo **Material Preview / Rendered** y renderizar con **F12**.

### T-Rex procedural (`BPYDINOSAUR.py`)

1. Abrir Blender 4.x → workspace **Scripting**.
2. Pegar/ejecutar el script completo (*Run Script*).
3. Características:
   - Cuerpo generado con secciones elípticas + músculos volumétricos, fusionado con **Remesh (Voxel)**.
   - Booleanos para cuencas oculares y fosas nasales (cutters visibles como wireframe, ocultos en render).
   - Modificadores no destructivos: Remesh, Smooth, Boolean, Subdivision, Displace.
   - Material de piel procedural con AO sutil.
   - Escena de estudio lista para render (CPU/GPU, 256 muestras, 1920×1080).
4. Ajustar los **parámetros al inicio del archivo** (limpieza, colección, render, geometría) según necesidad. `CLEAN_PREVIOUS = True` elimina objetos/colecciones previos con prefijos `TRex_` o `Studio_`.

## Notas

- `testt.py` es un borrador de pruebas; no forma parte del flujo principal.
- Los módulos usan `importlib.reload` en `main.py` para facilitar el desarrollo iterativo dentro de Blender.
