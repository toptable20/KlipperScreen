import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args, **kwargs):
    return ToolPanel(*args, **kwargs)


class ToolPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        printer = self._printer.get_printer_status_data()
        
        self.grid = Gtk.Grid()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        button_configs = [
            {"key": "move", "name": _("Move"), "panel": "move", "icon": "move"},
            {"key": "temperature", "name": _("Temp"), "panel": "temperature", "icon": "temperature"},
            {"key": "extrusion", "name": _("Extrusion"), "panel": "extrude", "icon": "extrusion"},
            {"key": "foodinkchange", "name": _("FoodInk Change"), "panel": "replacefoodink", "icon": "foodink_change"},
        ]

        self.buttons = {}

        for config in button_configs:
            key = config["key"]
            target_panel = config["panel"]
            display_name = config["name"]
            icon_name = config["icon"]

            button = self._gtk.Button(icon_name, display_name, "basic")
            self.buttons[key] = button
            
            button.set_size_request(100, 177)
            button.set_hexpand(False)
            button.set_halign(Gtk.Align.CENTER)
            button.set_valign(Gtk.Align.CENTER)
            
            try:
                panel_obj = self._screen.env.from_string(target_panel).render(printer)
                
                button.connect("clicked", self.menu_item_clicked, panel_obj, 
                            {"panel": target_panel, "name": display_name})
                
                box.pack_start(button, False, False, 0)
                logging.info(f"Button added: {key} -> Panel: {target_panel}")
                
            except Exception as e:
                logging.error(f"Failed to load panel '{target_panel}' for button '{key}': {e}")

        # self.items = self._config.get_menu_items("__main", "tool")
        # logging.info(f"self.items: {self.items}")

        # for i in range (len(self.items)):
        #     key = list(self.items[i])[0]
        #     item = self.items[i][key]

        #     name = self._screen.env.from_string(item['name']).render(printer)
        #     icon = self._screen.env.from_string(item['icon']).render(printer) if item['icon'] else None
        #     style = self._screen.env.from_string(item['style']).render(printer) if item['style'] else None
        #     logging.info(f"name {name}, icon {icon}, style {style}")

        #     b = self._gtk.Button(icon, name, style)

        #     panel = self._screen.env.from_string(item['panel']).render(printer)
        #     b.connect("clicked", self.menu_item_clicked, panel, item)

        #     self.labels[key] = b
        #     self.tool_menu.attach(self.labels[key], i, 0, 1, 1)

        # logging.info(f"self.labels: {self.labels}")

        # for button in self.buttons:
        #     button.connect("clicked", self._screen.show_panel(button[]))
        # self.content.add(self.tool_menu)

        # self.labels['tool'] = self.arrangeMenuItems(self.items, 4)
        
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        # box.set_spacing(26)
        self.grid.attach(box, 0, 0, 1, 1)
        
        box.set_hexpand(True)
        box.set_vexpand(True)
        self.content.add(self.grid)
        
        

    def process_busy(self, busy):
        for button in self.buttons:
            if button == "temperature":
                continue
            self.buttons[button].set_sensitive((not busy))
