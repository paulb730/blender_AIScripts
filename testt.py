import bpy 
import math










#create backdrop

bpy.ops.mesh.primitive_plane_add(size=26, 
                                 location=(5, 0, 0),
                                 rotation=(0, math.radians(90), 0))


#light 

bpy.ops.object.light_add(type='AREA',
                         location=(0, 0, 5),
)

bpy.context.object.data.energy=100

#create emitter object 

emitter_obj=bpy.ops.curve.primitive_bezier_circle_add(radius=1,
                                          rotation=(0,math.radians(90),0))

#emitter_obj=bpy.context.active_object
emitter_obj.data.bevel_depth=0.01
emitter_obj.data.extrude=0.02
emitter_obj.show_instance_for_render=False

#bpy.ops.object.convert(target='MESH')







