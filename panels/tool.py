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
            {"key": "foodinkchange", "name": _("FoodInk\nChange"), "panel": "replacefoodink", "icon": "foodink_change"},
        ]

        self.buttons = {}

        for config in button_configs:
            key = config["key"]
            target_panel = config["panel"]
            display_name = config["name"]
            icon_name = config["icon"]

            button = self._gtk.Button(icon_name, display_name, "top_menu")
            self.buttons[key] = button

            label = self._find_label_in_button(button)
            if label:
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                label.set_justify(Gtk.Justification.CENTER)
                if key == "foodinkchange":
                    label.set_width_chars(7)
                    label.set_max_width_chars(7)
                    label.set_lines(2)
            
            button.set_hexpand(False)
            button.set_halign(Gtk.Align.CENTER)
            button.set_valign(Gtk.Align.CENTER)
            
            try:
                panel_obj = self._screen.env.from_string(target_panel).render(printer)
                
                button.connect("clicked", self.menu_item_clicked, panel_obj, 
                            {"panel": target_panel, "name": display_name})
                
                box.pack_start(button, False, False, 13)
                logging.info(f"Button added: {key} -> Panel: {target_panel}")
                
            except Exception as e:
                logging.error(f"Failed to load panel '{target_panel}' for button '{key}': {e}")
        
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        home_button = Gtk.Button()
        home_button.get_style_context().add_class("home")

        home_icon_size = max(24, int(self._gtk.font_size * 1.8))
        image = self._gtk.Image("home", home_icon_size, home_icon_size)
        home_button.set_image(image)
        home_button.set_vexpand(False)
        home_button.set_hexpand(False)
        home_button.set_size_request(home_icon_size + 20, home_icon_size + 20)
        home_button.connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        header_box.pack_end(home_button, False, False, 0)

        self.grid.attach(header_box, 0, 0, 1, 1)
        self.grid.attach(box, 0, 0, 1, 20)
        
        box.set_hexpand(True)
        box.set_vexpand(True)
        self.content.add(self.grid)
        
    def _find_label_in_button(self, container):
        if isinstance(container, Gtk.Label):
            return container
        if hasattr(container, 'get_children'):
            for child in container.get_children():
                res = self._find_label_in_button(child)
                if res:
                    return res
        return None

    def process_busy(self, busy):
        for button in self.buttons:
            if button == "temperature":
                continue
            self.buttons[button].set_sensitive((not busy))
