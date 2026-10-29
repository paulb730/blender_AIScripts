import bpy 

def set_emitter(radius:float,rotation:tuple,bevel:float,extrude:float,render:bool):
    #create emitter object 

    bpy.ops.curve.primitive_bezier_circle_add(radius=radius,
                                          rotation=rotation)
    emitter_obj=bpy.context.active_object
    emitter_obj.data.bevel_depth=bevel
    emitter_obj.data.extrude=extrude
    #emitter_obj.show_instance_for_render=render
    bpy.ops.object.convert(target='MESH')