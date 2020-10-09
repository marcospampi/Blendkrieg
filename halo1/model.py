import bpy
import itertools
import math

from mathutils import Euler

from reclaimer.hek.defs.mode import mode_def
from reclaimer.hek.defs.mod2 import mod2_def
from reclaimer.model.jms import read_jms
from reclaimer.model.model_decompilation import extract_model
from reclaimer.util.geometry import point_distance_to_line

from ..constants import (JMS_VERSION_HALO_1, NODE_NAME_PREFIX,
	MARKER_NAME_PREFIX, VERY_SMALL_NUMBER, FAKE_NODE_PREFIX)
from ..scene.shapes import create_sphere, create_empty
from ..scene.util import (set_uniform_scale, reduce_vertices, trace_into_direction, generate_matrix, get_horizontal_direction, centroid_3d)
from ..scene.jms_util import (set_rotation_from_jms,
	set_translation_from_jms, get_absolute_node_transforms_from_jms)

def read_halo1model(filepath):
	'''Takes a halo1 model file and turns it into a jms object.'''

	# TODO: Use a tag handler to see if these files actually are what they
	# say they are. We can get really nasty parsing problems if they aren't.

	# These two model types can be imported the same way because of their
	# nearly matching structures when built into a python object.
	if (filepath.lower().endswith('.gbxmodel')
	or filepath.lower().endswith('.model')):
		# Load model
		tag = None
		if filepath.lower().endswith('.gbxmodel'):
			tag = mod2_def.build(filepath=filepath)
		else:
			tag = mode_def.build(filepath=filepath)
		#TODO: Get all lod permutations.
		#Only getting the superhigh perms for now
		jms = extract_model(tag.data.tagdata, write_jms=False)
		jms = list(filter(lambda m : m.lod_level == "superhigh",jms))
		return jms

	if filepath.lower().endswith('.jms'):
		# Read jms file into string.
		jms_string = ""
		with open(filepath, 'r') as jms_file:
			jms_string = jms_file.read()
		# Read Jms data from string.
		jms = read_jms(jms_string)
		# Make sure it's a Halo 1 jms
		if jms.version != JMS_VERSION_HALO_1:
			raise ValueError('Not a Halo 1 jms!')

		return [jms]


from mathutils import Vector

def import_halo1_nodes_from_jms(jms, *,
		scale=1.0,
		node_size=0.02,
		max_attachment_distance=0.00001,
		attach_bones=('bip01',),
		build_skeleton = False
		):
	'''
	Import all the nodes from a jms into the scene as an armature and returns
	a dict of them.

	node_size is currently unused and may be depricated.

	max_attachment_distance is the max distance a bone may deviate from
	the line that signifies the direction of the parent.

	attach_bones is a tuple of name prefixes that this function should attempt
	to connect.

	Returns the armature object and a dict of index - bone pairs.
	'''
	view_layer = bpy.context.view_layer

	scene_nodes = {}


	armature = bpy.data.armatures.new('imported')
	armature_obj = bpy.data.objects.new('imported', armature)

	# We need to specifically link the object to this so we can use mode_set
	# to set Blender to edit mode.

	view_layer.active_layer_collection.collection.objects.link(armature_obj)
	view_layer.objects.active = armature_obj

	# We need to be in edit mode in order to be able to edit armatures at all.

	edit_bones = armature.edit_bones
	bpy.ops.object.mode_set(mode='EDIT')



	for i, node in enumerate(jms.nodes):
		scene_node = edit_bones.new(name=NODE_NAME_PREFIX+node.name)

		# Assign parent if index is valid.
		scene_node.parent = scene_nodes.get(node.parent_index, None)

		M = generate_matrix(node,scale)
		scene_node.tail.y += 0.01
		if not scene_node.parent:
			scene_node.matrix = M
		else:
			scene_node.matrix = scene_node.parent.matrix @ M

		scene_nodes[i] = scene_node


	if build_skeleton == True:
		for node in scene_nodes.values():
			if node.parent and len(node.parent.children) == 1:
				node.parent.tail = node.head
				node.use_connect = True 
			elif node.parent and len(node.parent.children) > 1:
				node.parent.tail = centroid_3d(list(map(lambda c: c.head,node.parent.children)))
			#	node.use_connect = True

	node_custom_shape = create_empty(name="bone sphere",size=node_size)

	bpy.ops.object.mode_set(mode="POSE")
	if not build_skeleton:
		for bone in armature_obj.pose.bones:
			if bone.name[:1] == '$':
				continue
			bone.custom_shape = node_custom_shape
			bone.custom_shape_scale = node_size * 5

	bpy.ops.object.mode_set(mode="OBJECT")

	#view_layer.active_layer_collection.collection.objects.unlink(node_custom_shape)

	return armature_obj, scene_nodes

def import_halo1_markers_from_jms(jms, *, armature=None, scale=1.0, node_size=0.01,
		scene_nodes={}, import_radius=False,
		permutation_filter=(), region_filter=()
		):
	'''
	Import all the markers from a given jms into a scene.

	Will parent to the nodes from scene_nodes.

	Allows you to specify what permutations you would like to isolate using
	the permutation_filter. Same goes for regions.

	The option to import radius is off by default because this radius goes
	largely unused, and will just be a nuisance to people using the tool
	otherwise.
	'''
	# The number of regions in a jms model is always known,
	# so we can just create a default range.
	if not len(permutation_filter):
		# Do markers have a -1 no region state? Because this would not work if so.
		region_filter = range(len(jms.regions))
	markers = {}

	for i,marker in enumerate(jms.markers):
		# Permutations cannot be known without seeking through the whole model.
		# This is an easier way to deal with not being given a filter.
		if len(permutation_filter) and not (
				marker.permutation in permutation_filter):
			# Skip if not in one of the requested permutations.
			continue

		if not (marker.region in region_filter):
			# Skip if not in one of the requested regions.
			continue

		scene_marker = create_empty(
			name = MARKER_NAME_PREFIX + marker.name,
			size = scale if import_radius else node_size,
			display="SPHERE"
		)
		bpy.context.collection.objects.link(scene_marker)
		scene_marker.matrix_world = generate_matrix(marker, scale)

		# Assign parent if index is valid.
		parent = scene_nodes.get(marker.parent, None)
		if armature and parent:
			scene_marker.parent = armature
			scene_marker.parent_type = 'BONE'
			scene_marker.parent_bone = NODE_NAME_PREFIX+jms.nodes[marker.parent].name
			scene_marker.location.y -=  0.01 #parent.tail
		markers[i] = scene_marker

	#TODO: Should this return something? marco says YES
	return markers

def import_halo1_region_from_jms(jms, *,
		name="unnamed",
		scale=1.0,
		region_filter=(),
		parent_rig=None,
		skin_vertices=True):
	'''
	Imports all the geometry into a Halo 1 JMS into the scene.

	Only imports the regions in the region filter.

	mesh object gets linked to parent_rig and skinned to the bones if
	skin_vertices is True and the parent is an ARMATURE object.
	'''

	if not region_filter:
		region_filter = range(len(jms.regions))

	### Geometry preprocessing.

	# Ready the vertices.
	vertices = tuple(map(
			lambda v : (v.pos_x * scale, v.pos_y * scale, v.pos_z * scale),
			jms.verts
		)
	)

	# Ready the triangles.

	# Filter the triangles so only the wished regions are retrieved.
	triangles = tuple(filter(lambda t : t.region in region_filter, jms.tris))

	# Get the material index of each triangle.
	triangle_materials = tuple(map(lambda t : t.shader, triangles))

	# Reduce the triangles to just their key components.
	triangles = tuple(map(lambda t : (t.v0, t.v1, t.v2), triangles))

	# Unpack the vertex normals.
	vertex_normals = tuple(
		map(lambda v : (v.norm_i, v.norm_j, v.norm_k), jms.verts)
	)

	# Convert the vertex normals to triangle normals.
	tri_normals = map(
		lambda t : (
			vertex_normals[t[0]],
			vertex_normals[t[1]],
			vertex_normals[t[2]]),
		triangles
	)

	# Collect UVs

	vert_uvs = tuple(map(lambda v : (v.tex_u, v.tex_v), jms.verts))

	tri_uvs = tuple(map(
		lambda t : (
			vert_uvs[t[0]],
			vert_uvs[t[1]],
			vert_uvs[t[2]]),
		triangles
	))

	# Remove unused vertices
	vertices, triangles, translation_dict = reduce_vertices(vertices, triangles)

	# Chain all of the triangle normals together into loop normals.
	# ((x, y, z), (x, y, z), (x, y, z)), ((x, y, z), (x, y, z), (x, y, z)),
	#    |    |    |
	#    V    V    V
	# ((x, y, z), (x, y, z), (x, y, z), (x, y, z), (x, y, z), (x, y, z)),
	# Loops are the points of triangles so to speak.

	loop_normals = tuple(itertools.chain(*tri_normals))

	loop_uvs = tuple(itertools.chain(*tri_uvs))

	### Importing the data into a mesh

	# Make a mesh to hold all relevant data.
	mesh = bpy.data.meshes.new(name)

	# Import the verts and tris into the mesh.
	# verts, edges, tris. If () is given for edges Blender will infer them.
	mesh.from_pydata(vertices, (), triangles)

	# Add all materials from the jms to the mesh.
	for mat in jms.materials:
		mesh.materials.append(bpy.data.materials[mat.name])

	# Assign each triangle their corresponding material id.
	for i, poly in enumerate(mesh.polygons):
		poly.material_index = triangle_materials[i]

	# Import loop normals into the mesh.
	mesh.normals_split_custom_set(loop_normals)

	# Setting this to true makes Blender display the custom normals.
	# It feels really wrong. But it is right.
	mesh.use_auto_smooth = True

	# Apply the UVs

	for loop, uvs in zip(mesh.uv_layers.new().data, loop_uvs):
		loop.uv = uvs

	# Validate the mesh and make sure it doesn't have any invalid indices.
	mesh.validate()

	# Create the object, and link it to the scene.
	region_obj = bpy.data.objects.new(name, mesh)
	scene = bpy.context.collection
	scene.objects.link(region_obj)

	# If the function was supplied with a parent object attempt to skin to it
	# if it is an ARMATURE.

	region_obj.parent = parent_rig

	if skin_vertices and region_obj.parent.type == 'ARMATURE':
		mod = region_obj.modifiers.new('armature', 'ARMATURE')
		mod.object = parent_rig

		# Create a vertex group for each bone.

		for node in jms.nodes:
			region_obj.vertex_groups.new(name=NODE_NAME_PREFIX+node.name)

		# Add the vertices to all the correct vertex groups.

		for jms_i in translation_dict:
			v = jms.verts[jms_i]
			mesh_i = translation_dict[jms_i]

			if v.node_0 != -1:
				# The first node has no skinning data in JMS files (oof)
				if v.node_1 != -1:
					region_obj.vertex_groups[v.node_0].add(
						[mesh_i], 1.0 - v.node_1_weight, 'ADD')
				else:
					region_obj.vertex_groups[v.node_0].add(
						[mesh_i], 1.0, 'ADD')

			if v.node_1 != -1:
				region_obj.vertex_groups[v.node_1].add(
					[mesh_i], v.node_1_weight, 'ADD')

	return region_obj

def import_halo1_all_regions_from_jms(jms, *, name="", scale=1.0, parent_rig=None):
	'''
	Import all regions from a given jms.
	'''
	for i in range(len(jms.regions)):
		import_halo1_region_from_jms(
			jms,
			name=name+":"+jms.regions[i],
			scale=scale,
			region_filter=(i,),
			parent_rig=parent_rig
		)

def import_halo1_model_shader(name=""):
	if bpy.data.materials.get(name, None) is None:
		bpy.data.materials.new(name=name)

def build_skeleton(armature, markers = {}):
	return
	

