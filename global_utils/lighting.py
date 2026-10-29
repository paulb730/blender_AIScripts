import bpy 

def set_lighting(energy:float=100,
                 location:tuple=(0, 0, 5),type:str='AREA'):
    #light 
    bpy.ops.object.light_add(type=type,
                         location=location,
)
    bpy.context.object.data.energy=energy


