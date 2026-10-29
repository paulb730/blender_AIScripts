import bpy 

class Material:
    def __init__(self, nombre_material:str,**kwargs):
        self.nombre = nombre_material
        self.material=bpy.data.materials.new(name=self.nombre)


        self.material.use_nodes=True
        self.material_node_tree=self.material.node_tree

        for node in self.material_node_tree.nodes:
            self.material_node_tree.nodes.remove(node)


    def set_hair_nodes(self,mathops:str,emission_strenght:int,emission_color:tuple):
        self.current_nodelocation=0
        self.hair_info_node=self.material_node_tree.nodes.new("ShaderNodeHairInfo")
        self.current_nodelocation +=300

        self.color_ramp_node=self.material_node_tree.nodes.new("ShaderNodeValToRGB")
        self.color_ramp_node.color_ramp.interpolation="CONSTANT"
        self.color_ramp_node.location.x=self.current_nodelocation
        self.current_nodelocation+=300
        colorramp_cre_1=self.color_ramp_node.color_ramp.elements[1]
        colorramp_cre_1.position=0.98

        self.math_node=self.material_node_tree.nodes.new("ShaderNodeMath")
        self.math_node.location.x=self.current_nodelocation
        self.current_nodelocation+=300
        self.math_node.operation=mathops
        self.math_node.inputs[1].default_value=emission_strenght

        self.bsdf_node=self.material_node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        self.bsdf_node.location.x=self.current_nodelocation
        self.current_nodelocation+=300

        if emission_color:
            self.bsdf_node.inputs["Emission Color"].default_value=emission_color

        self.material_out_node=self.material_node_tree.nodes.new("ShaderNodeOutputMaterial")  
        self.material_out_node.location.x=self.current_nodelocation

        self.material_node_tree.links.new(
            self.bsdf_node.outputs["BSDF"],
            self.material_out_node.inputs["Surface"]
        )
        self.material_node_tree.links.new(
            self.hair_info_node.outputs["Random"],
            self.color_ramp_node.inputs["Fac"]
        )
        self.material_node_tree.links.new(
            self.color_ramp_node.outputs["Color"],
            self.math_node.inputs["Value"]
        )
        self.material_node_tree.links.new(
            self.math_node.outputs["Value"],
            self.bsdf_node.inputs["Emission Strength"]
        )



        

        


















