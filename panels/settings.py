import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from ks_includes.screen_panel import ScreenPanel
import logging


def create_panel(*args):
    return SettingsPanel(*args)


class SettingsPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        printer = self._printer.get_printer_status_data()
        
        self.grid = Gtk.Grid()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        button_configs = [
            {"key": "more", "name": _("More"), "panel": "more", "icon": "more", "scale": "2.0"},
            {"key": "network", "name": _("Network"), "panel": "network", "icon": "network", "scale": "3.0"},
            {"key": "autoleveling", "name": _("Auto\nLeveling"), "panel": "more", "icon": "auto_leveling", "scale": "2.0"},
        ]

        self.buttons = {}

        for config in button_configs:
            key = config["key"]
            target_panel = config["panel"]
            display_name = config["name"]
            icon_name = config["icon"]
            scale = float(config["scale"])

            button = self._gtk.Button(icon_name, display_name, "top_menu", scale=scale)
            self.buttons[key] = button

            label = self._find_label_in_button(button)
            if label:
                label.set_line_wrap(True)
                label.set_justify(Gtk.Justification.CENTER)
                label.set_max_width_chars(8)
            
            button.set_size_request(158, 177)
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
        # header_box.get_style_context().add_class("home")
        home_button = Gtk.Button()
        home_button.get_style_context().add_class("home")
        # home_button.set_name("home")
        image = self._gtk.Image("home", 40, 40)
        home_button.set_image(image)
        home_button.set_vexpand(False)
        home_button.set_hexpand(False)
        home_button.set_size_request(60, 60)
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
