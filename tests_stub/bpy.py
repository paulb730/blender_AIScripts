"""Stub minimo de bpy para pruebas fuera de Blender (valida enums)."""

ENUMS = {
    "ParticleSettings": {
        "type": {"EMITTER", "HAIR"},
        "physics_type": {"NEWTONIAN", "NEWBORN", "FIELD"},
        "distribution": {"RAND", "GRID", "JIT", "GROUP", "OLA"},
        "emit_from": {"VERT", "EDGE", "FACE", "VOLUME"},
        "render_type": {"NONE", "ORIG", "OBJECT", "PATH", "COLLECTION", "INSTANCE"},
    },
}


class _Items(list):
    """Lista que tambien expone atributos de stub (inputs["x"].default_value)."""

    def __getattr__(self, k):
        if k.startswith("_"):
            raise AttributeError(k)
        return _Node(f"items.{k}")


class _Node:
    """Nodo dinamico que valida enums si su nombre lo permite.

    Tambien es callable (devuelve un hijo), de modo que llamadas como
    ``bpy.data.materials.new(name=...)`` funcionen en el stub.
    """

    def __init__(self, name):
        self.__dict__["_nodename"] = name

    def __call__(self, *a, **kw):
        child = _Node(f"{self._nodename}.new")
        for k, v in kw.items():
            child.__dict__[k] = v
        return child

    def append(self, v):
        self.__dict__.setdefault("_items", _Items()).append(v)

    def clear(self):
        self.__dict__["_items"] = _Items()

    def remove(self, v):
        items = self.__dict__.get("_items", [])
        if v in items:
            items.remove(v)

    def __iter__(self):
        return iter(self.__dict__.get("_items", []))

    def __len__(self):
        return len(self.__dict__.get("_items", []))

    def __getitem__(self, i):
        items = self.__dict__.get("_items")
        if items is None:
            # Coleccion dinamica de stub (p.ej. color_ramp.elements):
            # se auto-puebla para que indexaciones [0]/[1] funcionen.
            items = _Items(_Node(f"{self._nodename}[{k}]") for k in range(8))
            self.__dict__["_items"] = items
        if isinstance(i, int):
            return items[i]
        return items

    def keys(self):
        return list(self.__dict__.get("_items", []))

    def __getattr__(self, k):
        if k.startswith("_"):
            raise AttributeError(k)
        child = _Node(f"{self._nodename}.{k}")
        self.__dict__[k] = child
        return child

    def __setattr__(self, k, v):
        base = self._nodename.split(".")[0]
        allowed = ENUMS.get(base, {}).get(k)
        if allowed and v not in allowed:
            raise ValueError(
                f"enum invalido {self._nodename}.{k}={v!r}; validos {sorted(allowed)}")
        self.__dict__[k] = v


class _Obj(_Node):
    def __init__(self, name="obj"):
        super().__init__(name)
        self.modifiers = []
        self.location = [0.0, 0.0, 0.0]
        self.rotation_euler = [0.0, 0.0, 0.0]
        self.scale = [1.0, 1.0, 1.0]
        self.name = name
        self.data = _Node("mesh")

    def select_set(self, v):
        if v:
            context.view_layer.objects.active = self
            context.selected_objects = [self]

    def convert(self, **kw):
        pass


class _Mod:
    def __init__(self, mtype, settings):
        self.type = mtype
        self.settings = settings


class ParticleSettings(_Node):
    def __init__(self, name="ParticleSettings"):
        super().__init__("ParticleSettings")
        self.name = name
        self.effector_weights = _Node("effector_weights")


_active_holder = {"obj": None}


class _Ops:
    def __init__(self):
        self.mesh = self
        self.object = self
        self.curve = self
        self.scene = self
        self.timeline = self
        self.render = self
        self.outliner = self
        self.view3d = self

    def _add_obj(self, name):
        o = _Obj(name)
        context.collection.objects.append(o)
        _active_holder["obj"] = o
        context.view_layer.objects.active = o
        context.selected_objects = [o]
        return o

    def primitive_grid_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Grid") else None

    def primitive_plane_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Plane") else None

    def primitive_bezier_circle_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Circle") else None

    def primitive_torus_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Torus") else None

    def primitive_uv_sphere_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Sphere") else None

    def light_add(self, type=None, location=(0, 0, 0), **kw):
        o = self._add_obj(f"Light_{type}")
        o.data = _Node("light")
        o.data.energy = 0.0
        return {"FINISHED"}

    def camera_add(self, location=(0, 0, 0), **kw):
        o = self._add_obj("Camera")
        o.data = _Node("camera")
        return {"FINISHED"}

    def primitive_cone_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Cone") else None

    def primitive_cylinder_add(self, **kw):
        return {"FINISHED"} if self._add_obj("Cylinder") else None

    def particle_system_add(self, **kw):
        obj = context.view_layer.objects.active
        psys = ParticleSettings(f"ParticleSettings.{len(obj.modifiers)}")
        obj.modifiers.append(_Mod("PARTICLE_SYSTEM", psys))
        return {"FINISHED"}

    def effector_add(self, type=None, location=(0, 0, 0), **kw):
        o = self._add_obj(f"Field_{type}")
        o.field = _Node("field")
        _active_holder["obj"] = o
        context.view_layer.objects.active = o
        return {"FINISHED"}

    def convert(self, target=None, **kw):
        return {"FINISHED"}

    def transform_apply(self, **kw):
        return {"FINISHED"}

    def select_all(self, action=None, **kw):
        if action == "DESELECT":
            context.selected_objects = []
        return {"FINISHED"}

    def shading_smooth(self, **kw):
        return {"FINISHED"}

    def shade_smooth(self, **kw):
        return {"FINISHED"}

    def frame_set(self, frame=None, **kw):
        context.scene.frame_current = frame
        return {"FINISHED"}

    def frame_change(self, **kw):
        return {"FINISHED"}

    def frames_render(self, **kw):
        return {"FINISHED"}

    def delete(self, **kw):
        return {"FINISHED"}

    def orphans_purge(self, **kw):
        return {"FINISHED"}

    def space_data_update(self, **kw):
        return {"FINISHED"}


class _ViewLayerObjects:
    active = None

    @staticmethod
    def update():
        pass


class _ViewLayer:
    objects = _ViewLayerObjects()


class _Collection:
    def __init__(self):
        self.objects = []
        self.collections = []

    def link(self, o):
        self.objects.append(o)

    def unlink(self, o):
        if o in self.objects:
            self.objects.remove(o)


class _Scene:
    def __init__(self):
        self.objects = []
        self.frame_start = 1
        self.frame_end = 250
        self.frame_current = 1
        self.render = _Node("render")
        self.cycles = _Node("cycles")
        self.evolution = _Node("evolution")
        self.collection = _Collection()

    def frame_set(self, frame=None, **kw):
        self.frame_current = frame


class _Context:
    def __init__(self):
        self.view_layer = _ViewLayer()
        self.scene = _Scene()
        self.collection = self.scene.collection
        self.selected_objects = []
        self.mode = "OBJECT"

    @property
    def object(self):
        return _active_holder["obj"]

    @property
    def active_object(self):
        return _active_holder["obj"]

    def view3d_update(self, **kw):
        pass

    def frame_set(self, frame=None, **kw):
        self.frame_current = frame


context = _Context()
ops = _Ops()
data = _Node("data")
data.objects = context.collection.objects
mesh = _Node("mesh")


class Collection(_Node):
    pass


types = _Node("types")
types.Collection = Collection


def update_depsgraph():
    pass
