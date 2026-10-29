# =============================================================================
# Blender 4.x - Improved Procedural T-Rex Studio Preview
# =============================================================================
#
# Mejoras principales:
#   - Cuerpo generado con secciones elípticas + músculos volumétricos.
#   - Fusionado orgánico mediante modificador Remesh (Voxel).
#   - Booleanos para cuencas oculares y fosas nasales.
#   - Modificadores no destructivos: Remesh, Smooth, Boolean, Subdivision, Displace.
#   - Cresta dorsal separada para mantener definición.
#   - Material de piel procedural mejorado con AO sutil.
#   - Escena de estudio lista para render en Cycles.
#
# Uso:
#   1. Abrir Blender 4.x
#   2. Workspace Scripting
#   3. Pegar este script completo
#   4. Run Script
#   5. Ver en Material Preview / Rendered
#   6. Renderizar con F12
#
# Notas:
#   - CLEAN_PREVIOUS = True elimina objetos/colecciones previos con prefijos
#     "TRex_" o "Studio_".
#   - Los cutters booleanos se mantienen visibles como wireframe y ocultos
#     en render. Puedes moverlos/escalarlos para cambiar cuencas/orificios.
# =============================================================================

import bpy
import bmesh
import math
from mathutils import Vector, Matrix


# =============================================================================
# PARÁMETROS AJUSTABLES
# =============================================================================

# Limpieza / organización
CLEAN_PREVIOUS = True
COLLECTION_NAME = "TRex_Studio"
CUTTERS_COLLECTION_NAME = "TRex_Cutters"

# Render
RENDER_DEVICE = "CPU"          # Cambia a "GPU" si tienes configuración GPU válida
RENDER_SAMPLES = 256
RENDER_RESOLUTION_X = 1920
RENDER_RESOLUTION_Y = 1080
EXPOSURE = 0.0

# Geometría del cuerpo / modificadores
REMESH_VOXEL_SIZE = 0.10
REMESH_SMOOTH_FACTOR = 0.40
REMESH_SMOOTH_ITERATIONS = 6

BODY_SUBDIV_VIEWPORT = 1
BODY_SUBDIV_RENDER = 1

DISPLACE_STRENGTH = 0.035
DISPLACE_NOISE_SCALE = 0.22

# Material de piel
SKIN_BASE_NOISE_SCALE = 3.0
SKIN_MACRO_VORONOI_SCALE = 26.0
SKIN_MICRO_VORONOI_SCALE = 110.0
SKIN_WRINKLE_NOISE_SCALE = 7.0
SKIN_FINE_NOISE_SCALE = 35.0
SKIN_ROUGHNESS_NOISE_SCALE = 10.0

# Cámara
CAMERA_LENS = 85.0
CAMERA_LOCATION = (-9.8, 28.5, 3.25)
CAMERA_TARGET = (0.0, 0.35, 2.85)
FOCUS_LOCATION = (0.0, 1.10, 3.15)
APERTURE_FSTOP = 5.6

# Luces
KEY_LOCATION = (-9.0, 12.0, 7.0)
KEY_TARGET = (0.0, 1.0, 3.0)
KEY_ENERGY = 3800.0
KEY_SIZE = 5.0
KEY_COLOR = (1.00, 0.82, 0.58)

FILL_LOCATION = (10.0, 11.0, 4.2)
FILL_TARGET = (0.0, 0.5, 2.8)
FILL_ENERGY = 950.0
FILL_SIZE = 8.0
FILL_COLOR = (0.92, 0.96, 1.00)

RIM_LOCATION = (2.0, -12.0, 8.0)
RIM_TARGET = (0.0, -2.0, 3.0)
RIM_ENERGY = 7500.0
RIM_SIZE = 3.0
RIM_COLOR = (0.75, 0.88, 1.00)

# Mundo
WORLD_COLOR = (0.008, 0.008, 0.010)
WORLD_STRENGTH = 0.08

# Posa / dedos
TOE_ANGLES = (-0.38, 0.0, 0.38)

# Cresta dorsal continua
CREST_TUBE = [
    ((0.0,  3.30, 4.35), (0.040, 0.080)),
    ((0.0,  2.80, 4.12), (0.050, 0.120)),
    ((0.0,  2.20, 3.95), (0.065, 0.180)),
    ((0.0,  1.40, 3.78), (0.080, 0.240)),
    ((0.0,  0.40, 3.45), (0.085, 0.260)),
    ((0.0, -0.80, 3.22), (0.080, 0.240)),
    ((0.0, -2.20, 3.02), (0.070, 0.200)),
    ((0.0, -4.20, 2.68), (0.055, 0.150)),
    ((0.0, -6.00, 2.50), (0.040, 0.100)),
    ((0.0, -7.20, 2.60), (0.025, 0.060)),
]

# Púas / espinas dorsales
SPINE_CREST = [
    ((0.0,  3.30, 4.38), 0.050, 0.14),
    ((0.0,  2.80, 4.16), 0.070, 0.20),
    ((0.0,  2.20, 4.02), 0.090, 0.28),
    ((0.0,  1.40, 3.86), 0.110, 0.36),
    ((0.0,  0.40, 3.52), 0.120, 0.42),
    ((0.0, -0.80, 3.28), 0.110, 0.36),
    ((0.0, -2.20, 3.06), 0.090, 0.28),
    ((0.0, -4.20, 2.72), 0.070, 0.20),
    ((0.0, -6.00, 2.54), 0.050, 0.14),
    ((0.0, -7.20, 2.63), 0.035, 0.09),
]


# =============================================================================
# HELPERS GENERALES
# =============================================================================

def safe_set(obj, attr, value):
    """Set attribute if it exists, ignoring version differences."""
    try:
        setattr(obj, attr, value)
    except Exception:
        pass


def rgba(color):
    """Return RGBA tuple from RGB/RGBA input."""
    if len(color) >= 4:
        return (float(color[0]), float(color[1]), float(color[2]), float(color[3]))
    return (float(color[0]), float(color[1]), float(color[2]), 1.0)


def set_socket(socket, value):
    """Set a node socket value robustly."""
    if socket is None:
        return False
    try:
        if socket.type == 'VALUE':
            socket.default_value = float(value)
        elif socket.type == 'VECTOR':
            if len(value) == 2:
                value = (value[0], value[1], 0.0)
            socket.default_value = (float(value[0]), float(value[1]), float(value[2]))
        elif socket.type == 'RGBA':
            socket.default_value = rgba(value)
        else:
            socket.default_value = value
        return True
    except Exception:
        return False


def set_principled(bsdf, aliases, value):
    """Set Principled BSDF input using possible Blender 3.x/4.x names."""
    if isinstance(aliases, str):
        aliases = [aliases]
    for name in aliases:
        sock = bsdf.inputs.get(name)
        if sock is not None and set_socket(sock, value):
            return True
    return False


def new_node(nt, node_type, location, label=""):
    """Create shader node with location and label."""
    node = nt.nodes.new(node_type)
    node.location = location
    if label:
        node.label = label
    return node


def get_or_create_material(name):
    """Get material by name or create it."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat


def get_or_create_collection(name):
    """Get collection by name or create and link to scene collection."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)

    scene_coll = bpy.context.scene.collection
    if coll.name not in [c.name for c in scene_coll.children]:
        try:
            scene_coll.children.link(coll)
        except Exception:
            pass

    return coll


def get_or_create_cloud_texture(name, noise_scale, noise_depth=2):
    """Get or create legacy Clouds texture for Displace modifier."""
    tex = bpy.data.textures.get(name)
    if tex is None:
        tex = bpy.data.textures.new(name, type='CLOUDS')
    safe_set(tex, 'noise_scale', float(noise_scale))
    safe_set(tex, 'noise_depth', int(noise_depth))
    return tex


def assign_material(obj, mat):
    """Assign one material to object mesh."""
    if obj is None or obj.data is None:
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def aim_at(obj, target):
    """Rotate object so local -Z points to target."""
    direction = Vector(target) - Vector(obj.location)
    if direction.length < 1e-6:
        return
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def parent_to_root(obj, root):
    """Parent object to root preserving transform when root is identity."""
    if obj is None or root is None:
        return
    obj.parent = root
    obj.matrix_parent_inverse = Matrix.Identity(4)


def cleanup_previous():
    """Remove previous TRex_/Studio_ objects and collections."""
    prefixes = ("TRex_", "Studio_")

    for ob in list(bpy.data.objects):
        if ob.name == "Cube" or any(ob.name.startswith(p) for p in prefixes):
            try:
                bpy.data.objects.remove(ob, do_unlink=True)
            except Exception:
                pass

    for coll in list(bpy.data.collections):
        if any(coll.name.startswith(p) for p in prefixes):
            for user_coll in list(coll.users_collection):
                try:
                    user_coll.children.unlink(coll)
                except Exception:
                    pass
            try:
                bpy.data.collections.remove(coll)
            except Exception:
                pass

    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except TypeError:
        try:
            bpy.data.orphans_purge()
        except Exception:
            pass
    except Exception:
        pass


# =============================================================================
# BMESH HELPERS
# =============================================================================

def bm_to_object(name, bm, coll, smooth=True):
    """Convert bmesh to Blender object linked into collection."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()

    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)

    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True

    return ob


def add_ring(bm, center, tangent, rx, rz, segments):
    """Create an elliptical ring perpendicular to tangent."""
    center = Vector(center)
    tangent = Vector(tangent)
    if tangent.length < 1e-6:
        tangent = Vector((0.0, 1.0, 0.0))
    tangent.normalize()

    up_hint = Vector((0.0, 0.0, 1.0))
    if abs(tangent.dot(up_hint)) > 0.98:
        up_hint = Vector((0.0, 1.0, 0.0))

    right = tangent.cross(up_hint).normalized()
    up = right.cross(tangent).normalized()

    rx = max(0.001, float(rx))
    rz = max(0.001, float(rz))
    seg = max(3, int(segments))

    verts = []
    for i in range(seg):
        a = 2.0 * math.pi * float(i) / float(seg)
        p = center + right * (math.cos(a) * rx) + up * (math.sin(a) * rz)
        verts.append(bm.verts.new(p))

    return verts


def bridge_rings(bm, ring_a, ring_b):
    """Bridge two rings with quads."""
    n = min(len(ring_a), len(ring_b))
    if n < 3:
        return

    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new((ring_a[i], ring_a[j], ring_b[j], ring_b[i]))
        except ValueError:
            pass


def cap_ring(bm, ring, reverse=False):
    """Cap a ring with an n-gon."""
    if len(ring) < 3:
        return
    verts = list(reversed(ring)) if reverse else list(ring)
    try:
        bm.faces.new(verts)
    except ValueError:
        pass


def add_path_tube(bm, points, radii, segments=12, cap_start=True, cap_end=True):
    """
    Create a tapered tube along a polyline.
    radii can be scalar or (rx, rz) elliptical semi-axes.
    """
    if len(points) < 2:
        return

    points = [Vector(p) for p in points]
    radii = list(radii)

    if len(radii) < len(points):
        while len(radii) < len(points):
            radii.append(radii[-1] if radii else 0.1)
    elif len(radii) > len(points):
        radii = radii[:len(points)]

    rings = []

    for i, p in enumerate(points):
        if i == 0:
            tang = points[1] - p
        elif i == len(points) - 1:
            tang = p - points[-2]
        else:
            tang = points[i + 1] - points[i - 1]

        if tang.length < 1e-6:
            tang = Vector((0.0, 1.0, 0.0))

        r = radii[i]
        if isinstance(r, (int, float)):
            rx = rz = float(r)
        else:
            rx = float(r[0])
            rz = float(r[1])

        rings.append(add_ring(bm, p, tang, rx, rz, segments))

    for i in range(len(rings) - 1):
        bridge_rings(bm, rings[i], rings[i + 1])

    if cap_start:
        cap_ring(bm, rings[0], reverse=True)
    if cap_end:
        cap_ring(bm, rings[-1], reverse=False)


def add_cone(bm, location, direction, radius1, radius2, depth, segments=12):
    """Add a cone/tapered cylinder. direction points toward radius2."""
    dirv = Vector(direction)
    if dirv.length < 1e-6:
        dirv = Vector((0.0, 0.0, 1.0))
    else:
        dirv.normalize()

    quat = dirv.to_track_quat('Z', 'Y')
    mat = Matrix.Translation(Vector(location)) @ quat.to_matrix().to_4x4()

    res = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=max(3, int(segments)),
        radius1=max(0.0001, float(radius1)),
        radius2=max(0.0, float(radius2)),
        depth=max(0.001, float(depth)),
    )

    bmesh.ops.transform(bm, matrix=mat, verts=res['verts'])


def add_sphere(bm, location, radius, segments=16, rings=8, scale=(1.0, 1.0, 1.0)):
    """Add UV sphere with optional non-uniform scale."""
    res = bmesh.ops.create_uvsphere(
        bm,
        u_segments=max(4, int(segments)),
        v_segments=max(3, int(rings)),
        radius=max(0.0001, float(radius)),
    )

    sx = max(0.0001, float(scale[0]))
    sy = max(0.0001, float(scale[1]))
    sz = max(0.0001, float(scale[2]))

    mat = (
        Matrix.Translation(Vector(location))
        @ Matrix.Diagonal((sx, sy, sz, 1.0))
    )

    bmesh.ops.transform(bm, matrix=mat, verts=res['verts'])


def add_mirrored_sphere(bm, x, y, z, scale, segments=16, rings=8):
    """Add sphere on +X and -X, or single sphere if x is near zero."""
    if abs(float(x)) < 1e-5:
        add_sphere(bm, (0.0, y, z), 1.0, segments, rings, scale)
    else:
        add_sphere(bm, ( float(x), y, z), 1.0, segments, rings, scale)
        add_sphere(bm, (-float(x), y, z), 1.0, segments, rings, scale)


def create_cutter_sphere(name, coll, location, scale, segments=16, rings=8):
    """Create a hidden wire sphere used as Boolean cutter."""
    bm = bmesh.new()
    add_sphere(bm, location, 1.0, segments, rings, scale)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    ob = bm_to_object(name, bm, coll, smooth=True)
    ob.display_type = 'WIRE'
    safe_set(ob, 'hide_render', True)
    safe_set(ob, 'visible_shadow', False)
    return ob


# =============================================================================
# MATERIALES
# =============================================================================

def create_basic_material(
    name,
    base_color,
    roughness=0.5,
    metallic=0.0,
    sss_weight=0.0,
    sss_radius=(1.0, 0.35, 0.18),
    sss_scale=0.04,
    coat_weight=0.0,
    specular=0.5,
):
    """Simple Principled material for teeth, eyes, mouth, backdrop."""
    mat = get_or_create_material(name)
    nt = mat.node_tree
    nt.nodes.clear()

    out = new_node(nt, 'ShaderNodeOutputMaterial', (400, 0), 'Material Output')
    bsdf = new_node(nt, 'ShaderNodeBsdfPrincipled', (100, 0), 'Principled BSDF')

    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    set_socket(bsdf.inputs.get('Base Color'), rgba(base_color))
    set_socket(bsdf.inputs.get('Roughness'), roughness)
    set_socket(bsdf.inputs.get('Metallic'), metallic)
    set_principled(bsdf, ['Specular IOR Level', 'Specular'], specular)

    if sss_weight > 0.0:
        set_principled(bsdf, ['Subsurface Weight', 'Subsurface'], sss_weight)
        set_principled(bsdf, ['Subsurface Radius'], sss_radius)
        set_principled(bsdf, ['Subsurface Scale'], sss_scale)

    if coat_weight > 0.0:
        set_principled(bsdf, ['Coat Weight', 'Clearcoat'], coat_weight)

    return mat


def create_skin_material():
    """
    Procedural T-Rex skin:
      - Earthy brown base
      - Lighter belly / darker dorsal area
      - Voronoi macro + micro scales
      - Noise wrinkles and fine grain
      - Chained bump
      - Subtle SSS
      - AO multiplying crevice darkening
    """
    mat = get_or_create_material("TRex_Skin_Procedural")
    nt = mat.node_tree
    nt.nodes.clear()

    out = new_node(nt, 'ShaderNodeOutputMaterial', (1800, 0), 'Material Output')
    bsdf = new_node(nt, 'ShaderNodeBsdfPrincipled', (1450, 0), 'Principled BSDF')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    set_principled(bsdf, ['Metallic'], 0.0)
    set_principled(bsdf, ['Specular IOR Level', 'Specular'], 0.35)
    set_principled(bsdf, ['Coat Weight', 'Clearcoat'], 0.03)

    # Subsurface scattering
    set_principled(bsdf, ['Subsurface Weight', 'Subsurface'], 0.09)
    set_principled(bsdf, ['Subsurface Radius'], (0.70, 0.28, 0.14))
    set_principled(bsdf, ['Subsurface Scale'], 0.035)
    set_principled(bsdf, ['Subsurface Color'], (0.45, 0.18, 0.08))

    texco = new_node(nt, 'ShaderNodeTexCoord', (-1800, 0), 'Texture Coordinate')
    mapping = new_node(nt, 'ShaderNodeMapping', (-1600, 0), 'Mapping')
    nt.links.new(texco.outputs['Object'], mapping.inputs['Vector'])
    set_socket(mapping.inputs.get('Scale'), (1.0, 1.0, 1.0))

    # ------------------------------------------------------------------
    # Base brown noise
    # ------------------------------------------------------------------
    noise_base = new_node(nt, 'ShaderNodeTexNoise', (-1350, 450), 'Base Noise')
    nt.links.new(mapping.outputs['Vector'], noise_base.inputs['Vector'])
    set_socket(noise_base.inputs.get('Scale'), SKIN_BASE_NOISE_SCALE)
    set_socket(noise_base.inputs.get('Detail'), 6.0)
    set_socket(noise_base.inputs.get('Roughness'), 0.62)
    set_socket(noise_base.inputs.get('Distortion'), 0.15)

    ramp_base = new_node(nt, 'ShaderNodeValToRGB', (-1100, 450), 'Brown Ramp')
    cr = ramp_base.color_ramp
    cr.interpolation = 'LINEAR'

    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.045, 0.024, 0.014, 1.0)

    cr.elements[1].position = 1.0
    cr.elements[1].color = (0.210, 0.120, 0.065, 1.0)

    e1 = cr.elements.new(0.48)
    e1.color = (0.110, 0.060, 0.032, 1.0)

    e2 = cr.elements.new(0.80)
    e2.color = (0.160, 0.090, 0.048, 1.0)

    nt.links.new(noise_base.outputs['Fac'], ramp_base.inputs['Fac'])

    # ------------------------------------------------------------------
    # Belly / dorsal masks from geometry normal
    # ------------------------------------------------------------------
    geo = new_node(nt, 'ShaderNodeNewGeometry', (-1350, 50), 'Geometry')
    sep_xyz = new_node(nt, 'ShaderNodeSeparateXYZ', (-1150, 50), 'Separate XYZ')
    nt.links.new(geo.outputs['Normal'], sep_xyz.inputs['Vector'])

    neg_z = new_node(nt, 'ShaderNodeMath', (-950, 50), 'Negate Normal Z')
    neg_z.operation = 'MULTIPLY'
    nt.links.new(sep_xyz.outputs['Z'], neg_z.inputs[0])
    set_socket(neg_z.inputs[1], -1.0)

    belly_range = new_node(nt, 'ShaderNodeMapRange', (-780, 50), 'Belly Mask')
    safe_set(belly_range, 'use_clamp', True)
    nt.links.new(neg_z.outputs[0], belly_range.inputs['Value'])
    set_socket(belly_range.inputs.get('From Min'), 0.0)
    set_socket(belly_range.inputs.get('From Max'), 1.0)
    set_socket(belly_range.inputs.get('To Min'), 0.0)
    set_socket(belly_range.inputs.get('To Max'), 1.0)

    top_range = new_node(nt, 'ShaderNodeMapRange', (-780, -150), 'Dorsal Mask')
    safe_set(top_range, 'use_clamp', True)
    nt.links.new(sep_xyz.outputs['Z'], top_range.inputs['Value'])
    set_socket(top_range.inputs.get('From Min'), 0.0)
    set_socket(top_range.inputs.get('From Max'), 1.0)
    set_socket(top_range.inputs.get('To Min'), 0.0)
    set_socket(top_range.inputs.get('To Max'), 1.0)

    top_strength = new_node(nt, 'ShaderNodeMath', (-580, -150), 'Dorsal Strength')
    top_strength.operation = 'MULTIPLY'
    nt.links.new(top_range.outputs['Result'], top_strength.inputs[0])
    set_socket(top_strength.inputs[1], 0.35)

    mix_belly = new_node(nt, 'ShaderNodeMixRGB', (-520, 300), 'Belly Mix')
    mix_belly.blend_type = 'MIX'
    nt.links.new(ramp_base.outputs['Color'], mix_belly.inputs['Color1'])
    nt.links.new(belly_range.outputs['Result'], mix_belly.inputs['Fac'])
    set_socket(mix_belly.inputs.get('Color2'), (0.390, 0.285, 0.175, 1.0))

    mix_dorsal = new_node(nt, 'ShaderNodeMixRGB', (-300, 300), 'Dorsal Mix')
    mix_dorsal.blend_type = 'MIX'
    nt.links.new(mix_belly.outputs['Color'], mix_dorsal.inputs['Color1'])
    nt.links.new(top_strength.outputs[0], mix_dorsal.inputs['Fac'])
    set_socket(mix_dorsal.inputs.get('Color2'), (0.035, 0.020, 0.012, 1.0))

    # ------------------------------------------------------------------
    # Voronoi scales
    # ------------------------------------------------------------------
    vor_macro = new_node(nt, 'ShaderNodeTexVoronoi', (-1350, -350), 'Voronoi Macro')
    safe_set(vor_macro, 'voronoi_dimensions', '3D')
    safe_set(vor_macro, 'feature', 'F1')
    safe_set(vor_macro, 'distance_metric', 'EUCLIDEAN')
    safe_set(vor_macro, 'randomness', 0.75)
    nt.links.new(mapping.outputs['Vector'], vor_macro.inputs['Vector'])
    set_socket(vor_macro.inputs.get('Scale'), SKIN_MACRO_VORONOI_SCALE)

    macro_range = new_node(nt, 'ShaderNodeMapRange', (-1100, -350), 'Macro Range')
    safe_set(macro_range, 'use_clamp', True)
    nt.links.new(vor_macro.outputs['Distance'], macro_range.inputs['Value'])
    set_socket(macro_range.inputs.get('From Min'), 0.05)
    set_socket(macro_range.inputs.get('From Max'), 0.70)
    set_socket(macro_range.inputs.get('To Min'), 0.0)
    set_socket(macro_range.inputs.get('To Max'), 1.0)

    vor_micro = new_node(nt, 'ShaderNodeTexVoronoi', (-1350, -600), 'Voronoi Micro')
    safe_set(vor_micro, 'voronoi_dimensions', '3D')
    safe_set(vor_micro, 'feature', 'F1')
    safe_set(vor_micro, 'distance_metric', 'EUCLIDEAN')
    safe_set(vor_micro, 'randomness', 0.55)
    nt.links.new(mapping.outputs['Vector'], vor_micro.inputs['Vector'])
    set_socket(vor_micro.inputs.get('Scale'), SKIN_MICRO_VORONOI_SCALE)

    micro_range = new_node(nt, 'ShaderNodeMapRange', (-1100, -600), 'Micro Range')
    safe_set(micro_range, 'use_clamp', True)
    nt.links.new(vor_micro.outputs['Distance'], micro_range.inputs['Value'])
    set_socket(micro_range.inputs.get('From Min'), 0.08)
    set_socket(micro_range.inputs.get('From Max'), 0.62)
    set_socket(micro_range.inputs.get('To Min'), 0.0)
    set_socket(micro_range.inputs.get('To Max'), 1.0)

    # ------------------------------------------------------------------
    # Scale crease darkening
    # ------------------------------------------------------------------
    crease_micro = new_node(nt, 'ShaderNodeMath', (-850, -500), 'Crease Micro')
    crease_micro.operation = 'MULTIPLY'
    nt.links.new(micro_range.outputs['Result'], crease_micro.inputs[0])
    set_socket(crease_micro.inputs[1], 0.38)

    crease_macro = new_node(nt, 'ShaderNodeMath', (-850, -650), 'Crease Macro')
    crease_macro.operation = 'MULTIPLY'
    nt.links.new(macro_range.outputs['Result'], crease_macro.inputs[0])
    set_socket(crease_macro.inputs[1], 0.16)

    crease_sum = new_node(nt, 'ShaderNodeMath', (-650, -575), 'Crease Sum')
    crease_sum.operation = 'ADD'
    nt.links.new(crease_micro.outputs[0], crease_sum.inputs[0])
    nt.links.new(crease_macro.outputs[0], crease_sum.inputs[1])

    mix_crease = new_node(nt, 'ShaderNodeMixRGB', (-50, 250), 'Scale Crease Mix')
    mix_crease.blend_type = 'MIX'
    nt.links.new(mix_dorsal.outputs['Color'], mix_crease.inputs['Color1'])
    nt.links.new(crease_sum.outputs[0], mix_crease.inputs['Fac'])
    set_socket(mix_crease.inputs.get('Color2'), (0.020, 0.012, 0.008, 1.0))

    # ------------------------------------------------------------------
    # AO for crevices / sockets
    # ------------------------------------------------------------------
    ao = new_node(nt, 'ShaderNodeAmbientOcclusion', (-100, 50), 'AO')
    safe_set(ao, 'only_local', True)
    set_socket(ao.inputs.get('Distance'), 0.35)

    mix_ao = new_node(nt, 'ShaderNodeMixRGB', (150, 250), 'AO Multiply')
    mix_ao.blend_type = 'MULTIPLY'
    set_socket(mix_ao.inputs.get('Fac'), 0.35)
    nt.links.new(mix_crease.outputs['Color'], mix_ao.inputs['Color1'])
    nt.links.new(ao.outputs['Color'], mix_ao.inputs['Color2'])

    nt.links.new(mix_ao.outputs['Color'], bsdf.inputs['Base Color'])

    # ------------------------------------------------------------------
    # Roughness variation
    # ------------------------------------------------------------------
    noise_rough = new_node(nt, 'ShaderNodeTexNoise', (-1350, -900), 'Roughness Noise')
    nt.links.new(mapping.outputs['Vector'], noise_rough.inputs['Vector'])
    set_socket(noise_rough.inputs.get('Scale'), SKIN_ROUGHNESS_NOISE_SCALE)
    set_socket(noise_rough.inputs.get('Detail'), 4.0)
    set_socket(noise_rough.inputs.get('Roughness'), 0.55)

    rough_range = new_node(nt, 'ShaderNodeMapRange', (-1100, -900), 'Roughness Range')
    safe_set(rough_range, 'use_clamp', True)
    nt.links.new(noise_rough.outputs['Fac'], rough_range.inputs['Value'])
    set_socket(rough_range.inputs.get('From Min'), 0.0)
    set_socket(rough_range.inputs.get('From Max'), 1.0)
    set_socket(rough_range.inputs.get('To Min'), 0.42)
    set_socket(rough_range.inputs.get('To Max'), 0.80)

    nt.links.new(rough_range.outputs['Result'], bsdf.inputs['Roughness'])

    # ------------------------------------------------------------------
    # Height fields
    # ------------------------------------------------------------------
    noise_wrinkle = new_node(nt, 'ShaderNodeTexNoise', (-1350, -1150), 'Wrinkle Noise')
    nt.links.new(mapping.outputs['Vector'], noise_wrinkle.inputs['Vector'])
    set_socket(noise_wrinkle.inputs.get('Scale'), SKIN_WRINKLE_NOISE_SCALE)
    set_socket(noise_wrinkle.inputs.get('Detail'), 8.0)
    set_socket(noise_wrinkle.inputs.get('Roughness'), 0.55)

    wrinkle_h = new_node(nt, 'ShaderNodeMath', (-1100, -1150), 'Wrinkle Height')
    wrinkle_h.operation = 'MULTIPLY'
    nt.links.new(noise_wrinkle.outputs['Fac'], wrinkle_h.inputs[0])
    set_socket(wrinkle_h.inputs[1], 0.50)

    noise_fine = new_node(nt, 'ShaderNodeTexNoise', (-1350, -1400), 'Fine Noise')
    nt.links.new(mapping.outputs['Vector'], noise_fine.inputs['Vector'])
    set_socket(noise_fine.inputs.get('Scale'), SKIN_FINE_NOISE_SCALE)
    set_socket(noise_fine.inputs.get('Detail'), 4.0)
    set_socket(noise_fine.inputs.get('Roughness'), 0.50)

    fine_h = new_node(nt, 'ShaderNodeMath', (-1100, -1400), 'Fine Height')
    fine_h.operation = 'MULTIPLY'
    nt.links.new(noise_fine.outputs['Fac'], fine_h.inputs[0])
    set_socket(fine_h.inputs[1], 0.16)

    macro_h = new_node(nt, 'ShaderNodeMath', (-850, -350), 'Macro Height')
    macro_h.operation = 'MULTIPLY'
    nt.links.new(macro_range.outputs['Result'], macro_h.inputs[0])
    set_socket(macro_h.inputs[1], 0.22)

    micro_h = new_node(nt, 'ShaderNodeMath', (-850, -600), 'Micro Height')
    micro_h.operation = 'MULTIPLY'
    nt.links.new(micro_range.outputs['Result'], micro_h.inputs[0])
    set_socket(micro_h.inputs[1], 0.34)

    height_a = new_node(nt, 'ShaderNodeMath', (-850, -1275), 'Height Add A')
    height_a.operation = 'ADD'
    nt.links.new(wrinkle_h.outputs[0], height_a.inputs[0])
    nt.links.new(fine_h.outputs[0], height_a.inputs[1])

    height_b = new_node(nt, 'ShaderNodeMath', (-650, -1100), 'Height Add B')
    height_b.operation = 'ADD'
    nt.links.new(height_a.outputs[0], height_b.inputs[0])
    nt.links.new(macro_h.outputs[0], height_b.inputs[1])

    # ------------------------------------------------------------------
    # Bump chain
    # ------------------------------------------------------------------
    bump_major = new_node(nt, 'ShaderNodeBump', (650, -900), 'Bump Major')
    set_socket(bump_major.inputs.get('Strength'), 0.45)
    set_socket(bump_major.inputs.get('Distance'), 0.025)
    set_socket(bump_major.inputs.get('Invert'), False)
    nt.links.new(height_b.outputs[0], bump_major.inputs['Height'])

    bump_micro = new_node(nt, 'ShaderNodeBump', (950, -900), 'Bump Micro')
    set_socket(bump_micro.inputs.get('Strength'), 0.28)
    set_socket(bump_micro.inputs.get('Distance'), 0.006)
    set_socket(bump_micro.inputs.get('Invert'), False)
    nt.links.new(micro_h.outputs[0], bump_micro.inputs['Height'])
    nt.links.new(bump_major.outputs['Normal'], bump_micro.inputs['Normal'])

    nt.links.new(bump_micro.outputs['Normal'], bsdf.inputs['Normal'])

    return mat


# =============================================================================
# GEOMETRÍA MEJORADA DEL T-REX
# =============================================================================

def create_trex_body(coll, cutters_coll):
    """
    Build the main organic T-Rex body as overlapping volumes:
      - torso / tail / neck
      - upper skull / snout
      - lower jaw in roaring pose
      - throat
      - legs / feet / toe bases
      - arms / hands
      - muscle masses

    Returns:
        body object
        list of boolean cutter objects
    """
    bm = bmesh.new()

    # ------------------------------------------------------------------
    # Torso, tail, neck, skull base
    # ------------------------------------------------------------------
    torso_points = [
        (0.0, -7.95, 2.55),
        (0.0, -7.10, 2.42),
        (0.0, -6.20, 2.32),
        (0.0, -5.10, 2.24),
        (0.0, -3.90, 2.22),
        (0.0, -2.80, 2.30),
        (0.0, -1.80, 2.38),
        (0.0, -0.80, 2.45),
        (0.0,  0.20, 2.55),
        (0.0,  1.10, 2.80),
        (0.0,  1.85, 3.08),
        (0.0,  2.55, 3.45),
        (0.0,  3.10, 3.82),
        (0.0,  3.45, 4.08),
    ]

    torso_radii = [
        (0.05, 0.05),
        (0.14, 0.13),
        (0.26, 0.23),
        (0.38, 0.33),
        (0.52, 0.45),
        (0.68, 0.58),
        (0.82, 0.70),
        (0.91, 0.78),
        (0.98, 0.84),
        (1.02, 0.88),
        (0.88, 0.80),
        (0.68, 0.62),
        (0.58, 0.54),
        (0.62, 0.58),
    ]

    add_path_tube(bm, torso_points, torso_radii, segments=18, cap_start=True, cap_end=True)

    # ------------------------------------------------------------------
    # Upper skull / snout
    # ------------------------------------------------------------------
    upper_points = [
        (0.0, 3.35, 4.10),
        (0.0, 3.75, 4.22),
        (0.0, 4.20, 4.32),
        (0.0, 4.70, 4.40),
        (0.0, 5.15, 4.44),
        (0.0, 5.45, 4.40),
    ]

    upper_radii = [
        (0.58, 0.56),
        (0.60, 0.62),
        (0.54, 0.58),
        (0.44, 0.48),
        (0.28, 0.32),
        (0.12, 0.12),
    ]

    add_path_tube(bm, upper_points, upper_radii, segments=16, cap_start=True, cap_end=True)

    # ------------------------------------------------------------------
    # Lower jaw, open roaring pose
    # ------------------------------------------------------------------
    lower_points = [
        (0.0, 3.45, 3.92),
        (0.0, 3.85, 3.82),
        (0.0, 4.30, 3.62),
        (0.0, 4.75, 3.38),
        (0.0, 5.05, 3.22),
    ]

    lower_radii = [
        (0.38, 0.22),
        (0.38, 0.21),
        (0.32, 0.18),
        (0.24, 0.14),
        (0.12, 0.09),
    ]

    add_path_tube(bm, lower_points, lower_radii, segments=14, cap_start=True, cap_end=True)

    # ------------------------------------------------------------------
    # Throat / gular region
    # ------------------------------------------------------------------
    throat_points = [
        (0.0, 3.15, 3.72),
        (0.0, 3.70, 3.62),
        (0.0, 4.30, 3.45),
        (0.0, 4.85, 3.32),
    ]

    throat_radii = [
        (0.42, 0.18),
        (0.38, 0.16),
        (0.28, 0.12),
        (0.14, 0.08),
    ]

    add_path_tube(bm, throat_points, throat_radii, segments=14, cap_start=True, cap_end=True)

    # ------------------------------------------------------------------
    # Legs, feet, toe bases
    # ------------------------------------------------------------------
    for sx in (1.0, -1.0):
        leg_points = [
            (sx * 0.68, -2.25, 2.05),
            (sx * 0.88, -1.55, 1.62),
            (sx * 1.08, -0.72, 1.10),
            (sx * 1.04, -1.05, 0.68),
            (sx * 0.96, -1.38, 0.38),
            (sx * 0.98, -0.85, 0.22),
            (sx * 1.02, -0.28, 0.13),
        ]

        leg_radii = [
            (0.42, 0.46),
            (0.40, 0.42),
            (0.26, 0.28),
            (0.22, 0.24),
            (0.17, 0.18),
            (0.15, 0.16),
            (0.20, 0.14),
        ]

        add_path_tube(bm, leg_points, leg_radii, segments=14, cap_start=True, cap_end=True)

        # Toe bases, will be fused by Remesh
        foot = Vector((sx * 1.02, -0.28, 0.13))
        for ang in TOE_ANGLES:
            dirv = Vector((math.sin(ang), math.cos(ang), 0.0)).normalized()
            base = foot + dirv * 0.10 + Vector((0.0, 0.0, 0.025))
            loc = base + dirv * 0.18
            add_cone(bm, loc, dirv, 0.10, 0.045, 0.36, segments=10)

    # ------------------------------------------------------------------
    # Arms / hands
    # ------------------------------------------------------------------
    for sx in (1.0, -1.0):
        arm_points = [
            (sx * 0.58, 1.35, 2.78),
            (sx * 0.82, 1.72, 2.32),
            (sx * 0.78, 2.05, 2.08),
            (sx * 0.80, 2.22, 2.00),
        ]

        arm_radii = [
            (0.20, 0.20),
            (0.14, 0.14),
            (0.10, 0.10),
            (0.07, 0.07),
        ]

        add_path_tube(bm, arm_points, arm_radii, segments=12, cap_start=True, cap_end=True)

        # Small hand mass
        add_sphere(bm, (sx * 0.80, 2.24, 1.98), 0.075, 12, 8, (1.0, 1.2, 0.8))

    # ------------------------------------------------------------------
    # Muscle masses
    # Each entry: (abs_x, y, z, scale_x, scale_y, scale_z)
    # ------------------------------------------------------------------
    muscle_defs = [
        # Thighs / legs
        (0.90, -1.55, 1.62, 0.42, 0.72, 0.52),
        (1.04, -0.95, 0.78, 0.26, 0.50, 0.58),
        (0.96, -1.32, 0.50, 0.18, 0.28, 0.22),

        # Shoulders / chest / arms
        (0.62,  1.28, 2.82, 0.28, 0.42, 0.30),
        (0.34,  1.50, 2.58, 0.26, 0.42, 0.28),

        # Flanks / abdomen
        (0.55, -0.65, 2.18, 0.32, 0.62, 0.42),

        # Neck
        (0.30,  2.85, 3.68, 0.18, 0.42, 0.28),
        (0.24,  3.25, 3.95, 0.14, 0.32, 0.20),

        # Tail base
        (0.30, -3.20, 2.35, 0.26, 0.58, 0.34),

        # Head details
        (0.36,  3.95, 4.42, 0.12, 0.22, 0.10),  # brow
        (0.42,  3.92, 3.98, 0.14, 0.28, 0.18),  # cheek / jowl
        (0.18,  4.70, 4.35, 0.16, 0.28, 0.12),  # snout side/top
    ]

    for x, y, z, sx, sy, sz in muscle_defs:
        add_mirrored_sphere(bm, x, y, z, (sx, sy, sz), segments=16, rings=8)

    # Midline throat muscle / chin bulge
    add_sphere(bm, (0.0, 3.55, 3.78), 1.0, 14, 8, (0.22, 0.30, 0.14))
    add_sphere(bm, (0.0, 4.25, 3.50), 1.0, 14, 8, (0.18, 0.35, 0.10))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    body = bm_to_object("TRex_Body", bm, coll, smooth=True)

    # ------------------------------------------------------------------
    # Boolean cutters: eye sockets and nostrils
    # ------------------------------------------------------------------
    cutters = []

    for sx in (1.0, -1.0):
        side = "L" if sx > 0.0 else "R"

        # Eye socket cutter
        cutters.append(
            create_cutter_sphere(
                f"TRex_Cutter_EyeSocket_{side}",
                cutters_coll,
                (sx * 0.48, 3.98, 4.32),
                (0.18, 0.20, 0.16),
                segments=18,
                rings=10,
            )
        )

        # Nostril cutter
        cutters.append(
            create_cutter_sphere(
                f"TRex_Cutter_Nostril_{side}",
                cutters_coll,
                (sx * 0.16, 5.05, 4.70),
                (0.055, 0.085, 0.055),
                segments=14,
                rings=8,
            )
        )

    return body, cutters


def add_body_modifiers(body, cutters):
    """
    Add non-destructive modifier stack to fuse and refine the body.
    Order:
      Remesh -> Smooth -> Boolean cutters -> Subdivision -> Displace
    """
    # Remesh: fuses overlapping organic volumes
    remesh = body.modifiers.new("Remesh", 'REMESH')
    remesh.mode = 'VOXEL'
    safe_set(remesh, 'voxel_size', REMESH_VOXEL_SIZE)
    safe_set(remesh, 'use_smooth_shade', True)
    safe_set(remesh, 'adaptivity', 0.0)

    # Smooth: reduces voxel stair-stepping before boolean cuts
    smooth = body.modifiers.new("RemeshSmooth", 'SMOOTH')
    safe_set(smooth, 'factor', REMESH_SMOOTH_FACTOR)
    safe_set(smooth, 'iterations', REMESH_SMOOTH_ITERATIONS)

    # Boolean cutters: eye sockets / nostrils
    for cutter in cutters:
        mod = body.modifiers.new(f"Boolean_{cutter.name}", 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = cutter
        safe_set(mod, 'use_hole_tolerant', True)
        safe_set(mod, 'use_self', False)

    # Subdivision: final smoothing for render
    sub = body.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = BODY_SUBDIV_VIEWPORT
    sub.render_levels = BODY_SUBDIV_RENDER
    safe_set(sub, 'use_limit_surface', True)

    # Displace: subtle skin irregularity
    tex = get_or_create_cloud_texture("TRex_Body_Displace", DISPLACE_NOISE_SCALE, 2)
    disp = body.modifiers.new("Displace", 'DISPLACE')
    disp.texture = tex
    disp.strength = DISPLACE_STRENGTH
    disp.mid_level = 0.5
    safe_set(disp, 'texture_coords', 'LOCAL')


def create_spine_crest(coll):
    """
    Create dorsal crest membrane + spikes as a separate object
    to keep them more defined than if fully remeshed.
    """
    bm = bmesh.new()

    crest_points = [p for p, r in CREST_TUBE]
    crest_radii = [r for p, r in CREST_TUBE]

    add_path_tube(
        bm,
        crest_points,
        crest_radii,
        segments=10,
        cap_start=True,
        cap_end=True,
    )

    for pt, base_r, depth in SPINE_CREST:
        tail_factor = max(0.0, min(1.0, (-float(pt[1]) - 1.0) / 7.0))
        dirv = Vector((0.0, -0.12 - 0.25 * tail_factor, 1.0)).normalized()
        loc = Vector(pt) + dirv * (depth * 0.45)
        add_cone(bm, loc, dirv, base_r, 0.0, depth, segments=8)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    spine = bm_to_object("TRex_SpineCrest", bm, coll, smooth=True)

    # Light bevel to avoid razor edges but keep silhouette crisp
    bev = spine.modifiers.new("Bevel", 'BEVEL')
    safe_set(bev, 'width', 0.004)
    safe_set(bev, 'segments', 2)
    safe_set(bev, 'limit_method', 'ANGLE')
    safe_set(bev, 'angle_limit', math.radians(40.0))
    safe_set(bev, 'use_clamp_overlap', True)

    return spine



def create_mouth_interior(coll):
    """Dark mouth interior visible in the open roar."""
    bm = bmesh.new()

    mouth_points = [
        (0.0, 3.50, 3.98),
        (0.0, 4.00, 3.86),
        (0.0, 4.50, 3.62),
        (0.0, 4.95, 3.38),
    ]

    mouth_radii = [
        (0.30, 0.055),
        (0.28, 0.050),
        (0.22, 0.040),
        (0.12, 0.030),
    ]

    add_path_tube(
        bm,
        mouth_points,
        mouth_radii,
        segments=12,
        cap_start=True,
        cap_end=True,
    )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object("TRex_MouthInterior", bm, coll, smooth=True)


def create_teeth_and_claws(coll):
    """Upper/lower teeth, hand claws and toe claws."""
    bm = bmesh.new()

    ub = Vector((0.0, 3.55, 4.02))
    uf = Vector((0.0, 5.25, 4.32))

    lb = Vector((0.0, 3.55, 3.88))
    lf = Vector((0.0, 5.00, 3.25))

    tooth_count = 10

    uw_back, uw_front = 0.52, 0.20
    uh_back, uh_front = 0.56, 0.22

    lw_back, lw_front = 0.34, 0.11
    lh_back, lh_front = 0.22, 0.09

    for side in (1.0, -1.0):
        for i in range(tooth_count):
            t = 0.10 + (float(i) / float(tooth_count - 1)) * 0.82
            sin_t = math.sin(math.pi * t)

            # Upper teeth
            c = ub + (uf - ub) * t
            w = uw_back + (uw_front - uw_back) * t
            h = uh_back + (uh_front - uh_back) * t
            bottom_z = c.z - h * 0.5 + 0.025

            pos = Vector((side * w * 0.82, c.y, bottom_z))
            dirv = Vector((side * 0.35, 0.12, -1.0)).normalized()

            depth = 0.16 + 0.08 * sin_t
            rad = 0.030 + 0.008 * sin_t
            loc = pos + dirv * (depth * 0.45)

            add_cone(bm, loc, dirv, rad, 0.0, depth, segments=8)

            # Lower teeth
            c2 = lb + (lf - lb) * t
            w2 = lw_back + (lw_front - lw_back) * t
            h2 = lh_back + (lh_front - lh_back) * t
            top_z = c2.z + h2 * 0.5 - 0.020

            pos2 = Vector((side * w2 * 0.82, c2.y, top_z))
            dirv2 = Vector((side * 0.22, -0.08, 1.0)).normalized()

            depth2 = 0.13 + 0.05 * sin_t
            rad2 = 0.026 + 0.006 * sin_t
            loc2 = pos2 + dirv2 * (depth2 * 0.45)

            add_cone(bm, loc2, dirv2, rad2, 0.0, depth2, segments=8)

        # Hand claw
        hand = Vector((side * 0.80, 2.22, 2.00))
        claw_dir = Vector((side * 0.18, 0.70, -0.70)).normalized()
        add_cone(bm, hand + claw_dir * 0.05, claw_dir, 0.035, 0.0, 0.12, segments=8)

    # Toe claws
    for sx in (1.0, -1.0):
        foot = Vector((sx * 1.02, -0.28, 0.13))
        for ang in TOE_ANGLES:
            dirv = Vector((math.sin(ang), math.cos(ang), 0.0)).normalized()
            tip = foot + dirv * 0.45
            claw_dir = (dirv * 0.55 + Vector((0.0, 0.0, 0.82))).normalized()
            add_cone(bm, tip + claw_dir * 0.055, claw_dir, 0.042, 0.0, 0.15, segments=8)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object("TRex_Teeth_Claws", bm, coll, smooth=True)


def create_eyes(coll):
    """Glossy eyes placed in the boolean sockets."""
    bm = bmesh.new()

    for sx in (1.0, -1.0):
        add_sphere(
            bm,
            (sx * 0.44, 3.98, 4.30),
            0.082,
            segments=18,
            rings=10,
            scale=(2.0, 2.0, 2.0),
        )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object("TRex_Eyes", bm, coll, smooth=True)


# =============================================================================
# BACKDROP DE ESTUDIO
# =============================================================================

def create_backdrop(coll):
    """Curved studio cyclorama."""
    bm = bmesh.new()

    x_half = 35.0
    profile = []

    # Floor
    for y in (45.0, 30.0, 15.0, 5.0, -2.0, -7.0, -10.0):
        profile.append((y, 0.0))

    # Cove
    radius = 8.0
    steps = 16
    for i in range(1, steps + 1):
        a = (math.pi / 2.0) * (float(i) / float(steps))
        y = -10.0 - radius * math.sin(a)
        z = radius - radius * math.cos(a)
        profile.append((y, z))

    # Back wall
    for z in (10.0, 16.0, 24.0, 32.0):
        profile.append((-18.0, z))

    rows = []
    for y, z in profile:
        vl = bm.verts.new((-x_half, y, z))
        vr = bm.verts.new(( x_half, y, z))
        rows.append((vl, vr))

    for i in range(len(rows) - 1):
        l1, r1 = rows[i]
        l2, r2 = rows[i + 1]
        try:
            bm.faces.new((l1, l2, r2, r1))
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_object("Studio_Backdrop", bm, coll, smooth=True)


# =============================================================================
# LUSES, CÁMARA, MUNDO
# =============================================================================

def add_area_light(name, coll, location, target, energy, size, color):
    """Create and aim an area light."""
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    safe_set(ld, 'shape', 'SQUARE')
    safe_set(ld, 'use_shadow', True)

    ob = bpy.data.objects.new(name, ld)
    coll.objects.link(ob)
    ob.location = location
    aim_at(ob, target)
    return ob


def create_lights(coll):
    """Three-point studio lighting."""
    key = add_area_light(
        "Studio_Key_Light",
        coll,
        KEY_LOCATION,
        KEY_TARGET,
        KEY_ENERGY,
        KEY_SIZE,
        KEY_COLOR,
    )

    fill = add_area_light(
        "Studio_Fill_Light",
        coll,
        FILL_LOCATION,
        FILL_TARGET,
        FILL_ENERGY,
        FILL_SIZE,
        FILL_COLOR,
    )

    rim = add_area_light(
        "Studio_Rim_Light",
        coll,
        RIM_LOCATION,
        RIM_TARGET,
        RIM_ENERGY,
        RIM_SIZE,
        RIM_COLOR,
    )

    return key, fill, rim


def create_camera_and_focus(coll):
    """85 mm camera with DOF focus target."""
    focus = bpy.data.objects.new("TRex_Focus_Target", None)
    coll.objects.link(focus)
    focus.location = FOCUS_LOCATION
    focus.empty_display_size = 0.25
    safe_set(focus, 'empty_display_type', 'PLAIN_AXES')

    cam_data = bpy.data.cameras.new("Studio_Camera")
    cam_data.lens = CAMERA_LENS
    cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 300.0

    cam = bpy.data.objects.new("Studio_Camera", cam_data)
    coll.objects.link(cam)
    cam.location = CAMERA_LOCATION
    aim_at(cam, CAMERA_TARGET)

    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = focus
    cam_data.dof.aperture_fstop = APERTURE_FSTOP

    bpy.context.scene.camera = cam

    return cam, focus


def setup_world():
    """Dark studio world."""
    world = bpy.data.worlds.get("Studio_World")
    if world is None:
        world = bpy.data.worlds.new("Studio_World")

    bpy.context.scene.world = world
    world.use_nodes = True

    nt = world.node_tree
    nt.nodes.clear()

    out = new_node(nt, 'ShaderNodeOutputWorld', (400, 0), 'World Output')
    bg = new_node(nt, 'ShaderNodeBackground', (100, 0), 'Background')

    set_socket(bg.inputs.get('Color'), rgba(WORLD_COLOR))
    set_socket(bg.inputs.get('Strength'), WORLD_STRENGTH)

    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


# =============================================================================
# RENDER
# =============================================================================

def configure_render():
    """Cycles high-quality preview settings."""
    sc = bpy.context.scene

    safe_set(sc.render, 'engine', 'CYCLES')

    try:
        sc.cycles.device = RENDER_DEVICE
    except Exception:
        try:
            sc.cycles.device = 'CPU'
        except Exception:
            pass

    safe_set(sc.cycles, 'samples', RENDER_SAMPLES)
    safe_set(sc.cycles, 'use_adaptive_sampling', True)
    safe_set(sc.cycles, 'adaptive_threshold', 0.01)

    safe_set(sc.cycles, 'use_denoising', True)
    safe_set(sc.cycles, 'use_preview_denoising', True)

    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass

    safe_set(sc.cycles, 'denoising_use_gpu', False)

    safe_set(sc.cycles, 'max_bounces', 8)
    safe_set(sc.cycles, 'diffuse_bounces', 4)
    safe_set(sc.cycles, 'glossy_bounces', 4)
    safe_set(sc.cycles, 'transmission_bounces', 4)
    safe_set(sc.cycles, 'volume_bounces', 0)

    safe_set(sc.render, 'resolution_x', RENDER_RESOLUTION_X)
    safe_set(sc.render, 'resolution_y', RENDER_RESOLUTION_Y)
    safe_set(sc.render, 'resolution_percentage', 100)
    safe_set(sc.render, 'film_transparent', False)

    try:
        sc.render.image_settings.file_format = 'PNG'
    except Exception:
        pass

    try:
        sc.view_settings.view_transform = 'AgX'
    except Exception:
        try:
            sc.view_settings.view_transform = 'Filmic'
        except Exception:
            pass

    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass

    safe_set(sc.view_settings, 'exposure', EXPOSURE)


# =============================================================================
# MAIN
# =============================================================================

def main():
    if CLEAN_PREVIOUS:
        cleanup_previous()

    coll = get_or_create_collection(COLLECTION_NAME)
    cutters_coll = get_or_create_collection(CUTTERS_COLLECTION_NAME)

    # Materials
    skin_mat = create_skin_material()

    tooth_mat = create_basic_material(
        "TRex_Tooth",
        base_color=(0.78, 0.72, 0.60),
        roughness=0.28,
        metallic=0.0,
        sss_weight=0.05,
        sss_radius=(0.80, 0.35, 0.18),
        sss_scale=0.025,
        specular=0.60,
    )

    eye_mat = create_basic_material(
        "TRex_Eye",
        base_color=(0.015, 0.012, 0.010),
        roughness=0.06,
        metallic=0.0,
        coat_weight=1.0,
        specular=0.70,
    )

    mouth_mat = create_basic_material(
        "TRex_Mouth",
        base_color=(0.12, 0.025, 0.025),
        roughness=0.75,
        metallic=0.0,
        sss_weight=0.12,
        sss_radius=(0.60, 0.15, 0.08),
        sss_scale=0.04,
        specular=0.35,
    )

    backdrop_mat = create_basic_material(
        "Studio_Backdrop_Mat",
        base_color=(0.022, 0.022, 0.025),
        roughness=0.55,
        metallic=0.0,
        specular=0.25,
    )

    # Root empty for whole dinosaur
    root = bpy.data.objects.new("TRex_Root", None)
    coll.objects.link(root)
    root.location = (0.0, 0.0, 0.0)
    root.empty_display_size = 1.0
    safe_set(root, 'empty_display_type', 'ARROWS')

    # Geometry
    body, cutters = create_trex_body(coll, cutters_coll)
    add_body_modifiers(body, cutters)

    spine = create_spine_crest(coll)
    mouth = create_mouth_interior(coll)
    teeth = create_teeth_and_claws(coll)
    eyes = create_eyes(coll)
    backdrop = create_backdrop(coll)

    # Materials
    assign_material(body, skin_mat)
    assign_material(spine, skin_mat)
    assign_material(mouth, mouth_mat)
    assign_material(teeth, tooth_mat)
    assign_material(eyes, eye_mat)
    assign_material(backdrop, backdrop_mat)

    # Parent dinosaur + cutters to root
    for ob in (body, spine, mouth, teeth, eyes):
        parent_to_root(ob, root)

    for ob in cutters:
        parent_to_root(ob, root)

    # Studio
    create_lights(coll)
    create_camera_and_focus(coll)
    setup_world()
    configure_render()

    try:
        bpy.context.view_layer.update()
    except Exception:
        pass

    print("Improved T-Rex procedural studio scene created successfully.")
    print("Select Studio_Camera and press Ctrl+Numpad0 for camera view.")
    print("Body modifiers: Remesh, Smooth, Boolean, Subdivision, Displace.")
    print("Cutter objects are hidden in render and displayed as wireframe.")


if __name__ == "__main__":
    main()