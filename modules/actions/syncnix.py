import bpy

bpy.ops.object.vertex_group_set_active(group='Template_SyncModel')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.delete(type='VERT')
bpy.ops.object.editmode_toggle()
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all()
bpy.ops.mesh.blend_from_shape(shape='Ah_1')
bpy.ops.mesh.blend_from_shape(shape='Ah_1')

bpy.ops.object.editmode_toggle()
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
bpy.context.object.active_shape_key_index = 16

