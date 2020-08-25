import bpy
import bmesh
from .util import set_active_object, get_active_object
def create_sphere(name="new_sphere", size=1.0, color = (1,1,1,1)):
	'''
	Creates a sphere with the given size and color.
	'''
	scene = bpy.context.collection

	mesh = bpy.data.meshes.new(name)
	sphere = bpy.data.objects.new(name, mesh)

	scene.objects.link(sphere)

	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm,
		u_segments=16, v_segments=16,
		diameter=size
	)
	bm.to_mesh(mesh)
	bm.free()

	material = bpy.data.materials.get(name)

	if not material:
		material = bpy.data.materials.new(name = name)
		material.diffuse_color = color
	sphere.data.materials.append(material)
	sphere.hide_render = True
	return sphere

def create_cone(name="new_cone", base_size=1.0, height=3.0):
	'''
	Creates a cone with the given sizes.
	'''
	scene = bpy.context.collection

	mesh = bpy.data.meshes.new(name)
	cone = bpy.data.objects.new(name, mesh)

	scene.objects.link(cone)

	bm = bmesh.new()
	bmesh.ops.create_cone(bm,
		segments=16,
		diameter1=base_size, diameter2=base_size,
		depth=height
	)
	bm.to_mesh(mesh)
	bm.free()

	return cone
def create_empty(name="empty",display="SPHERE", size =1.0):
	empty = bpy.data.objects.new(name,None)

	empty.empty_display_type = display
	empty.empty_display_size = size

	return empty
	