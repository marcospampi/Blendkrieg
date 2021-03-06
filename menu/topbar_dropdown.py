from bpy.utils import register_class, unregister_class
from bpy.types import Menu, TOPBAR_MT_editor_menus

from .import_export import halo1_model
from .import_export import halo1_anim

class TOPBAR_MT_krieg(Menu):
	bl_idname = "TOPBAR_MT_krieg_ext"
	bl_label = "Krieg"

	def draw(self, context):
		layout = self.layout

		layout.menu("TOPBAR_MT_krieg_import", icon='IMPORT')
		layout.menu("TOPBAR_MT_krieg_export", icon='EXPORT')

		layout.separator()

		layout.operator(
			"wm.url_open", text="Manual", icon='HELP'
		).url = "https://github.com/gbMichelle/Blendkrieg/wiki"
		layout.operator(
			"wm.url_open", text="GitHub", icon='URL'
		).url = "https://github.com/gbMichelle/Blendkrieg"


class TOPBAR_MT_krieg_import(Menu):
	bl_label = "Import"

	def draw(self, context):
		layout = self.layout

		# Halo 1:

		layout.operator(
			halo1_model.MT_krieg_ImportHalo1Model.bl_idname,
			text="Halo 1 Model (.gbxmodel, .model, .jms)"
		)

		layout.separator()

		# Whatever else:
		layout.operator(
			halo1_anim.MT_krieg_ImportHalo1Anim.bl_idname,
			text="Halo 1 Animation (.model_animations)"
		)


class TOPBAR_MT_krieg_export(Menu):
	bl_label = "Export"

	def draw(self, context):
		layout = self.layout

		# Halo 1:

		layout.separator()

		# Whatever else:


# Enumerate all classes for easy register/unregister.
classes = (
	TOPBAR_MT_krieg,
	TOPBAR_MT_krieg_import,
	TOPBAR_MT_krieg_export,
)

def draw_krieg_button(self, context):
	'''
	When appended to another menu class this
	function will execute after the built-in draw(),
	and draw the 'Krieg' button.
	'''
	self.layout.menu(TOPBAR_MT_krieg.bl_idname, text=TOPBAR_MT_krieg.bl_label)

def register():
	for cls in classes:
		register_class(cls)

	TOPBAR_MT_editor_menus.append(draw_krieg_button)

def unregister():
	TOPBAR_MT_editor_menus.remove(draw_krieg_button)

	for cls in reversed(classes): #Reversed because: first in, last out.
		unregister_class(cls)


if __name__ == "__main__":
	register()
