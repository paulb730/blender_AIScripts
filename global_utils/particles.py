import bpy


class Particle:
    def __init__(self, tipo, count):
        self.tipo = tipo
        self.count=count
        bpy.ops.object.particle_system_add()
        self.partsys=bpy.data.particles["ParticleSettings"]
        

    def set_particlesystem(self):
        
        self.partsys.type=self.tipo
        self.partsys.count=self.count


    def is_particle(self,
                    hair_length:float,
                    hair_step:int,
                    display_step:int,
                    render_step:int):
        self.set_particlesystem()
        if self.tipo == "HAIR":
            self.partsys.hair_length=hair_length
            self.partsys.hair_step=hair_step
            self.partsys.display_step=display_step
            self.partsys.render_step=render_step

    def set_force_field(self,force_tipo,location:tuple=(0,0,1.26),strength:float=25):
        bpy.ops.object.effector_add(type=force_tipo, location=location)
        bpy.context.object.field.strength=strength

    

        


