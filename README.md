# Custom Bench Command: Export Custom DocType

This custom CLI command converts database-only "Custom" DocTypes into "Standard" DocTypes. It generates the necessary schema JSON files, python/javascript controller boilerplates, and automatically extracts and exports associated Client Scripts and Server Scripts.

"Custom" DocTypes = is the doctype that created in erpnext UI, while develpoer mode is off/ producation, so the custom DT is created in Database without file directory exsistence 

"Standard" DocTypes = is the doctype that created in erpnext UI, while develpoer mode is on, and files are created automacilty in file doctype file directory
---

## Features
1. **Generic & Site-Aware:** Registered inside `frappe` core commands, making it usable in any Frappe/ERPNext project.
2. **Bulk Export:** Supports passing multiple DocType names at once.
3. **Client Script Extractor:** Finds enabled Client Scripts, exports them to the standard `[doctype_name].js` file, and disables them in the DB.
4. **Server Script Extractor:** Maps database Server Script events (e.g., `Before Save`, `After Save`) to python class methods (e.g., `before_save`, `on_update`), injects them into the controller `[doctype_name].py`, and disables them in the DB.

---

## Usage

```bash
bench --site [sitename] export-custom-doctype "[DocType Name 1]" "[DocType Name 2]" ...
```

### Example:
```bash
bench --site site1.local export-custom-doctype "students" "student path"
```

### Help Option:
```bash
bench export-custom-doctype --help
```
Output:
```text
Usage: bench export-custom-doctype [OPTIONS] DOCTYPE_NAME

  Converts a custom DocType to standard and exports it with all files.

Options:
  --help  Show this message and exit.
```

---

## Installtion Path

the utils.py is core file in frappe framwork, we need to insert this code to the current command lists so when it called from any where it will execute correctly with the default bench commands

The command is implemented globally in the `frappe` app's CLI utility file by updating 
`/root/frappe-bench/apps/frappe/frappe/commands/utils.py`

put this code at end lines of bench command codes then add it to commands list like this

commands = [
	export_custom_doctype,


