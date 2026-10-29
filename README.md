# VSAI Blender BPY

Proyecto de **automatización de escenas en Blender** mediante scripts Python (API `bpy`). Incluye dos flujos de trabajo:

1. **Escena procedural de partículas / pelo (main.py)** — configuración modular de entorno, emisores, sistemas de partículas y materiales.

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

1. Abrir Proyecto en VSCODE
2. Abrir y ejecutar `main.py` (*Run Script*). Debe estar junto a las carpetas `global_utils/` y `materials/`.
3. El script:
   - Limpia la escena (`helpers.clean_scene`).
   - Crea el fondo/backdrop, una luz de área y la cámara; ajusta resolución (1080×1080), 128 muestras y motor **CYCLES**.
   - Genera un emisor (círculo Bézier convertido a malla) con **8000 partículas de pelo** y un campo de fuerza **TURBULENCE**.
   - Crea el material `Hair_Material` con nodos de pelo (emisión roja multiplicada ×25).
4. Ver en modo **Material Preview / Rendered** y renderizar con **F12**.


## Notas

- `testt.py` es un borrador de pruebas; no forma parte del flujo principal.
- Los módulos usan `importlib.reload` en `main.py` para facilitar el desarrollo iterativo dentro de Blender.
