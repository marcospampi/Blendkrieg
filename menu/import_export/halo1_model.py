import bpy
import os
from bpy.utils import register_class, unregister_class
from bpy.props import BoolProperty, FloatProperty, StringProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper, orientation_helper, path_reference_mode, axis_conversion

from ...halo1.model import (
	read_halo1model,
	import_halo1_nodes_from_jms,
	import_halo1_markers_from_jms,
	import_halo1_all_regions_from_jms,
	import_halo1_model_shader,
	build_skeleton
)
from ...constants import SCALE_MULTIPLIERS

#@orientation_helper(axis_forward='-Z') Find the right value for this.
class MT_krieg_ImportHalo1Model(bpy.types.Operator, ImportHelper):
	"""
	The import operator for gbxmodel/jms models.
	This stores the properties when inside of the import dialog, and
	it specifies what to show on the side panel when importing.
	"""
	bl_idname = "import_scene.halo1_model"
	bl_label = "Import Halo 1 Model"
	bl_options = {'PRESET', 'UNDO'}

	# Import-file-dialog settings:

	filename_ext = ".gbxmodel"
	filter_glob: StringProperty(
		default="*.gbxmodel;*.model;*.jms",
		options={'HIDDEN'},
	)

	# Node settings:

	use_nodes: BoolProperty(
		name="Import Nodes",
		description="Import the nodes",
		default=True,
	)
	node_size: FloatProperty(
		name="Node Scene Size",
		description="Set the size that nodes should have in the Blender scene if at 1.0 scale.",
		default=0.1,
		min=0.0,
	)
	build_skeleton: BoolProperty(
		name="Build skeleton",
		description="Attach biped's nodes",
		default=False,
	)

	# Marker settings:

	use_markers: BoolProperty(
		name="Import Markers",
		description="Import the markers.",
		default=True,
	)
	marker_size: FloatProperty(
		name="Marker Scene Size",
		description="Set the size that markers should have in the Blender scene.",
		default=0.05,
		min=0.0,
	)

	# Scaling settings:

	scale_enum: EnumProperty(
	name="Scale",
		items=(
			('METRIC', "Blender",  "Use Blender's metric scaling."),
			('MAX',    "3ds Max",  "Use 3dsmax's 100xHalo scale."),
			('HALO',   "Internal", "Use Halo's internal 1.0 scale (small)."),
			('CUSTOM', "Custom",   "Set your own scaling multiplier."),
		)
	)
	scale_float: FloatProperty(
		name="Custom Scale",
		description="Set your own scale.",
		default=1.0,
		min=0.0,
	)

	def execute(self, context):
		# Set appropriate scaling
		scale = 1.0
		if self.scale_enum in SCALE_MULTIPLIERS:
			scale = SCALE_MULTIPLIERS[self.scale_enum]
		elif self.scale_enum == 'CUSTOM':
			scale = self.scale_float
		else:
			raise ValueError('Invalid scale_enum state.')

		# Test if jms import function doesn't crash.
		model = read_halo1model(self.filepath)

		# Get name without path or file extension.
		name = os.path.basename(os.path.splitext(self.filepath)[0])

		# Import nodes into the scene.
		armature, nodes = import_halo1_nodes_from_jms(model[0], scale=scale, node_size=self.node_size,build_skeleton=self.build_skeleton)
		# Import markers.
		markers = import_halo1_markers_from_jms(model[0], scale=scale,
			node_size=self.marker_size, armature=armature, scene_nodes=nodes)

		#for mat in [ mat for mat in ]:
		#	import_halo1_model_shader(mat.name)
		for jms in model:
			for mat in jms.materials:
				import_halo1_model_shader(mat.name)
		for jms in model:
			import_halo1_all_regions_from_jms(jms, name=name, scale=scale, parent_rig=armature)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout

		# Node settings elements:

		box = layout.box()
		row = box.row()
		row.label(text="Nodes:")
		row.prop(self, "use_nodes")
		if self.use_nodes:
			box.prop(self, "node_size")
			box.prop(self, "build_skeleton")

		# Marker settings elements:

		box = layout.box()
		row = box.row()
		row.label(text="Markers:")
		row.prop(self, "use_markers")
		if self.use_markers:
			box.prop(self, "node_size")

		# Scale settings elements:

		box = layout.box()
		box.label(text="Scale:")
		row = box.row()
		row.prop(self, "scale_enum", expand=True)

		if self.scale_enum == 'CUSTOM':
			row = box.row()
			row.prop(self, "scale_float")


# Enumerate all classes for easy register/unregister.
classes = (
	MT_krieg_ImportHalo1Model,
)

def register():
	for cls in classes:
		register_class(cls)


def unregister():
	#Unregister classes in reverse order to avoid any dependency problems.
	for cls in reversed(classes):
		unregister_class(cls)


if __name__ == "__main__":
	register()
