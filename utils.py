@click.command("export-custom-doctype")
@click.argument("doctype_names", nargs=-1, required=True)
@pass_context
def export_custom_doctype(context, doctype_names):
	"""Converts custom DocTypes to standard and exports them along with their client & server scripts."""
	import os
	import frappe
	import frappe.modules
	
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	for doctype_name in doctype_names:
		click.echo(f"Processing DocType: {doctype_name}...")
		
		if not frappe.db.exists("DocType", doctype_name):
			click.echo(f"Error: DocType '{doctype_name}' does not exist.", err=True)
			continue
			
		doc = frappe.get_doc("DocType", doctype_name)
		if not doc.custom:
			click.echo(f"DocType '{doctype_name}' is already a Standard DocType. Re-exporting...")
		else:
			# Convert and update custom flag in DB
			frappe.db.set_value("DocType", doctype_name, "custom", 0)
			frappe.db.commit()
			click.echo(f"Converted '{doctype_name}' to Standard DocType in DB.")

		# Save/Export the DocType (generates JSON, PY, JS, and test templates)
		doc = frappe.get_doc("DocType", doctype_name)
		doc.save()
		
		# Resolve the folder path
		scrubbed = frappe.scrub(doctype_name)
		module_path = frappe.modules.get_module_path(doc.module)
		doctype_folder = os.path.join(module_path, "doctype", scrubbed)
		
		# 1. CLIENT SCRIPTS EXPORT
		# Search for active Client Script records
		client_scripts = frappe.get_all(
			"Client Script",
			filters={"dt": doctype_name, "enabled": 1},
			fields=["name", "script"]
		)
		if client_scripts:
			js_path = os.path.join(doctype_folder, f"{scrubbed}.js")
			js_content = ""
			for cs in client_scripts:
				js_content += f"\n// Client Script: {cs.name}\n{cs.script}\n"
			
			with open(js_path, "w", encoding="utf-8") as f:
				f.write(js_content)
			click.echo(f"Exported {len(client_scripts)} Client Script(s) to {js_path}")
			
			# Disable client scripts in DB to avoid duplicate execution
			for cs in client_scripts:
				frappe.db.set_value("Client Script", cs.name, "enabled", 0)
			frappe.db.commit()
			click.echo("Disabled exported Client Scripts in the database.")
			
		# 2. SERVER SCRIPTS EXPORT
		# Search for active Server Script records
		server_scripts = frappe.get_all(
			"Server Script",
			filters={"reference_doctype": doctype_name, "disabled": 0},
			fields=["name", "doctype_event", "script"]
		)
		if server_scripts:
			py_path = os.path.join(doctype_folder, f"{scrubbed}.py")
			
			# Event mapping
			event_map = {
				"Before Insert": "before_insert",
				"Before Save": "before_save",
				"After Save": "on_update",
				"Before Submit": "before_submit",
				"After Submit": "on_submit",
				"Before Cancel": "before_cancel",
				"After Cancel": "on_cancel",
				"Before Delete": "before_delete",
				"After Delete": "on_trash",
				"After Insert": "after_insert",
			}
			
			with open(py_path, "r", encoding="utf-8") as f:
				py_content = f.read()
				
			lines = py_content.split("\n")
			class_decl_line = None
			for line in lines:
				if line.strip().startswith("class ") and "(Document)" in line:
					class_decl_line = line
					break
					
			if class_decl_line:
				methods_code = ""
				for ss in server_scripts:
					event_name = ss.get("doctype_event")
					method_name = event_map.get(event_name)
					if not method_name:
						click.echo(f"Warning: Event '{event_name}' in Server Script '{ss.name}' has no standard mapping.", err=True)
						continue
					
					script_body = ss.get("script")
					indented_body = "\n".join("        " + line for line in script_body.strip().split("\n"))
					methods_code += f"\n    def {method_name}(self):\n        doc = self\n        # Server Script: {ss.name}\n{indented_body}\n"
				
				parts = py_content.split(class_decl_line)
				body = parts[1]
				if body.strip() == "pass":
					body = ""
				parts[1] = methods_code + body
				py_content = class_decl_line.join(parts)
				
				with open(py_path, "w", encoding="utf-8") as f:
					f.write(py_content)
				click.echo(f"Exported {len(server_scripts)} Server Script(s) to {py_path}")
				
				for ss in server_scripts:
					frappe.db.set_value("Server Script", ss.name, "disabled", 1)
				frappe.db.commit()
				click.echo("Disabled exported Server Scripts in the database.")
				
		click.echo(f"Successfully processed DocType: {doctype_name}\n")
