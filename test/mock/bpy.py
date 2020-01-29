# A note on data types:
# Blender refers to most things in the scene as Objects. This includes meshes,
# cameras, lights, etc...
# This does NOT include collecions, which are their own thing.

# This module attempts to replicate Blender's API functionality, albeit with
# basic lists and dictionaries instead of whatever Blender is using.
# This should, in theory, be a drop-in replacement for testing.

from mathutils import Euler, Quaternion, Vector

class Data:
	def __init__(self):
		self.collections = dict() # All the collections in the scene
		self.meshes = dict()      # All the mesh objects in the scene
		self.objects = dict()     # All the objects in the scene

class Collection:
	def __init__(self):
		self.children = dict() # All sub-collections in this collection
		self.name = None       # Name as it appears in Outliner
		self.objects = dict()  # All objects in this collection

class Object:
	def __init__(self):
		self.children = list()         # Objects parented to this object
		self.location = Vector()       # Coordinate location of this object
		self.name = None               # Name as it appears in Outliner
		self.parent = None             # The object this object is parented to
		self.rotation_euler = Euler()  # Rotation in Euler coordinates
		self.rotation_mode = 'XYZ'     # Rotation mode (or Euler coordinate order)
		self.rotation_quaternion = Quaternion() # Rotation in Quaternion coordinates
		self.users_collection = set()  # All the collections this object belongs to


is_mock = True # Allows tests to verify they're using the mocks
data = Data()


def clear_mock():
	data.collections.clear()
	data.meshes.clear()
	data.objects.clear()

def set_scene_data(nested):
	'''Uses a nested dictionary to create all of the objects in the scene.
	Collections are created by name. Parents are inferred from dict structure.
	'''
	_add_objects(nested)

# Yeah, we're using recursion. Sue me
def _add_objects(nested, parent=None, parent_colls=set()):
	for name in nested:
		obj = Object()
		obj.name = name

		loc = nested[name].get('location', Vector())
		obj.location = Vector((loc[0], loc[1], loc[2]))

		rot = nested[name].get('rotation', Euler())
		if isinstance(rot, Euler):
			# FIXME This is hard-coded as XYZ for now because mathutils 2.81.2
			# doesn't support other orders for Euler coordinates.
			# TODO is this how Blender handles setting rotation for other modes?
			obj.rotation_mode = 'XYZ'
			obj.rotation_euler = rot
			obj.rotation_quaternion = rot.to_quaternion()
		elif isinstance(rot, Quaternion):
			obj.rotation_mode = 'QUATERNION'
			obj.rotation_quaternion = rot
			obj.rotation_euler = rot.to_euler()
		else:
			raise Exception('Invalid rotation type: ' + str(type(rot)))

		if parent:
			obj.parent = parent
			parent.children.append(obj)

		# Create any new collections
		child_colls = set()
		for coll_name in nested[name].get('collections', set()):
			coll = data.collections.get(coll_name)
			if coll is None:
				coll = Collection()
				coll.name = coll_name
				data.collections[coll_name] = coll
			child_colls.add(coll)

		# Add all child collections as children of parent collections
		for p_coll in parent_colls:
			for c_coll in child_colls:
				p_coll.children[c_coll.name] = c_coll

		# Set up associations between object and all relevant collections
		all_colls = child_colls | parent_colls
		for coll in all_colls:
			obj.users_collection.add(coll)
			coll.objects[name] = obj

		children = nested[name].get('children')
		if children:
			_add_objects(children, parent=obj, parent_colls=all_colls)

		data.objects[name] = obj
