import bpy


class Material:
    """Clase parametrica para crear y configurar materiales en Blender.

    Todos los valores que antes estaban hardcodeados (espaciado entre nodos,
    interpolacion del color ramp, posicion del crease, etc.) ahora son
    parametros con valores por defecto razonables.
    """

    # Valores por defecto de la clase (ajustables por instancia o por llamada)
    DEFAULT_NODE_SPACING = 300        # separacion horizontal entre nodos
    DEFAULT_RAMP_INTERP = "CONSTANT"  # interpolacion del ColorRamp
    DEFAULT_RAMP_POS = 0.98           # posicion del segundo elemento del ramp

    def __init__(self, nombre_material: str, *, node_spacing: int = DEFAULT_NODE_SPACING, **kwargs):
        self.nombre = nombre_material
        self.node_spacing = node_spacing
        self.material = bpy.data.materials.new(name=self.nombre)
        self.material.use_nodes = True
        self.material_node_tree = self.material.node_tree
        self._clear_nodes()

    # ------------------------------------------------------------------ #
    # Utilidades genericas
    # ------------------------------------------------------------------ #
    def _clear_nodes(self):
        """Elimina todos los nodos del arbol del material."""
        for node in list(self.material_node_tree.nodes):
            self.material_node_tree.nodes.remove(node)

    def add_node(self, node_type: str, location_x: float = 0, location_y: float = 0, name: str | None = None):
        """Crea un nodo del tipo dado en la ubicacion indicada."""
        node = self.material_node_tree.nodes.new(node_type)
        node.location = (location_x, location_y)
        if name:
            node.name = name
        return node

    def link(self, from_socket, to_socket):
        """Enlaza dos sockets (salida -> entrada)."""
        self.material_node_tree.links.new(from_socket, to_socket)

    # ------------------------------------------------------------------ #
    # Nodes especificos para pelo (hair emission)
    # ------------------------------------------------------------------ #
    def set_hair_nodes(
        self,
        mathops: str,
        emission_strenght: int,
        emission_color: tuple,
        *,
        ramp_interpolation: str = DEFAULT_RAMP_INTERP,
        ramp_position: float = DEFAULT_RAMP_POS,
        node_spacing: int | None = None,
    ):
        spacing = node_spacing if node_spacing is not None else self.node_spacing

        x = 0
        self.hair_info_node = self.add_node("ShaderNodeHairInfo", x)
        x += spacing

        self.color_ramp_node = self.add_node("ShaderNodeValToRGB", x)
        self.color_ramp_node.color_ramp.interpolation = ramp_interpolation
        self.color_ramp_node.color_ramp.elements[1].position = ramp_position
        x += spacing

        self.math_node = self.add_node("ShaderNodeMath", x)
        self.math_node.operation = mathops
        self.math_node.inputs[1].default_value = emission_strenght
        x += spacing

        self.bsdf_node = self.add_node("ShaderNodeBsdfPrincipled", x)
        if emission_color:
            self.bsdf_node.inputs["Emission Color"].default_value = emission_color
        x += spacing

        self.material_out_node = self.add_node("ShaderNodeOutputMaterial", x)

        # Enlaces del grafo
        self.link(self.hair_info_node.outputs["Random"], self.color_ramp_node.inputs["Fac"])
        self.link(self.color_ramp_node.outputs["Color"], self.math_node.inputs["Value"])
        self.link(self.math_node.outputs["Value"], self.bsdf_node.inputs["Emission Strength"])
        self.link(self.bsdf_node.outputs["BSDF"], self.material_out_node.inputs["Surface"])
