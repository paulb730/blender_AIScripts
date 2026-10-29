import bpy 


def clean_scene():
    # 1. Eliminar todos los objetos de la escena actual
    if bpy.context.scene.objects:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    for i in range(3):
        bpy.ops.outliner.orphans_purge(
        do_local_ids=True, 
        do_linked_ids=True, 
        do_recursive=True
                            )    

def set_scene(resolution:list=[1080, 1080],
              samples:int=128,
              device:str="GPU",
              render_engine:str="CYCLES",
              background_color:tuple=(1.0, 1.0, 1.0, 1.0)
              ):
    world_obj=bpy.data.worlds["World"]
    world_obj.node_tree.nodes["Background"].inputs["Color"].default_value=background_color
    #set background color to black

    bpy.context.scene.render.engine=render_engine
    bpy.context.scene.cycles.device=device
    bpy.context.scene.cycles.samples=samples
    

    bpy.context.scene.render.resolution_x=resolution[0]
    bpy.context.scene.render.resolution_y=resolution[1]

    

def set_camera(location:tuple=(0.0,0.0,0.0),
               rotation:tuple=(0,
                                    0,
                                    0),
                                    lens:int=35):
    #setup the camera
    bpy.ops.object.camera_add(location=location,
                          rotation=rotation)

    camera_obj=bpy.context.active_object
    camera_obj.data.lens=lens
    bpy.context.scene.camera=camera_obj

def create_backdrop(size:float=26,
                    location:tuple=(5, 0, 0),
                    rotation:tuple=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, 
                                 location=location,
                                 rotation=rotation)
    


