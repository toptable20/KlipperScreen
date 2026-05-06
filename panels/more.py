import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from ks_includes.screen_panel import ScreenPanel
from ks_includes.widgets.keypad import Keypad
from ks_includes.widgets.keyboard import Keyboard

import logging


class NumpadKeypad(Keypad):
    def update_entry(self, widget, digit):
        text = self.labels['entry'].get_text()
        if digit == 'B':
            if len(text) < 1:
                return
            self.labels['entry'].set_text(text[:-1])
        elif digit == 'E':
            if text is None or text is "":
                self.change_temp("0")
            else:
                self.change_temp(text)
            self.labels['entry'].set_text("")
        elif digit == 'PID':
            if self.pid_calibrate is not None:
                self.pid_calibrate(text)
            self.labels['entry'].set_text("")
        elif len(text + digit) > 3:
            return
        else:
            self.labels['entry'].set_text(text + digit)
        self.pid.set_sensitive(self.validate_temp(self.labels['entry'].get_text()) > 9)


def create_panel(*args):
    return MorePanel(*args)


class MorePanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.printers = self.settings = self.langs = {}
        self.menu = ['settings_menu']
        options = self._config.get_configurable_options().copy()
        options.append({"printers": {
            "name": _("Printer Connections"),
            "type": "menu",
            "menu": "printers"
        }})
        options.append({"lang": {
            "name": _("Language"),
            "type": "menu",
            "menu": "lang"
        }})

        ps = self._printer.get_stat("print_stats")
        remove_calibration = False
        # logging.info(f"ps: {ps}")
        if ps['available_camera'] is False:
            # logging.info("remove calibration option")
            remove_calibration = True
        
        detect_type = self._config.get_main_config().getint("detect_type", 0)
        
        bed_center_calibration_options = [
            'bed_center_calibration',
            'detect_type'
        ]

        # logging.info(f"detect_type: {detect_type}")
        
        if detect_type == 0:  # Circle
            bed_center_calibration_options.extend(['target_height', 'target_radius'])
        else:  # Unstructured (1)
            bed_center_calibration_options.extend(['target_height', 'target_number', 'print_sequence'])
        
        remove_bed_mesh = False
        if ps['available_bed_mesh'] is False:
            remove_bed_mesh = True

        bed_mesh_options = [
            'bed_mesh_on_print_start',
            'mesh_point'
        ]

        self.labels['settings_menu'] = self._gtk.ScrolledWindow()
        self.labels['settings_menu'].get_style_context().add_class("settings_menu")
        self.labels['settings'] = Gtk.Grid()
        self.labels['settings_menu'].add(self.labels['settings'])
        for option in options:
            name = list(option)[0]
            if remove_calibration and name in bed_center_calibration_options:
                # logging.info(f"pass {name}")
                continue

            if remove_bed_mesh and name in bed_mesh_options:
                # logging.info(f"pass {name}")
                continue

            self.add_option('settings', self.settings, name, option[name])

        self.labels['lang_menu'] = self._gtk.ScrolledWindow()
        self.labels['lang'] = Gtk.Grid()
        self.labels['lang'].get_style_context().add_class("settings_menu")
        self.labels['lang_menu'].add(self.labels['lang'])
        for lang in self._config.lang_list:
            self.langs[lang] = {
                "name": lang,
                "type": "lang",
            }
            self.add_option("lang", self.langs, lang, self.langs[lang])

        self.labels['printers_menu'] = self._gtk.ScrolledWindow()
        self.labels['printers'] = Gtk.Grid()
        self.labels['printers'].get_style_context().add_class("settings_menu")
        self.labels['printers_menu'].add(self.labels['printers'])
        for printer in self._config.get_printers():
            pname = list(printer)[0]
            self.printers[pname] = {
                "name": pname,
                "section": f"printer {pname}",
                "type": "printer",
                "moonraker_host": printer[pname]['moonraker_host'],
                "moonraker_port": printer[pname]['moonraker_port'],
            }
            self.add_option("printers", self.printers, pname, self.printers[pname])

        self.on_detect_type_changed(detect_type)

        self.content.add(self.labels['settings_menu'])

    def on_detect_type_changed(self, new_detect_type):
        """Handle detect_type changes (0=Circle, 1=Unstructured)"""
        if new_detect_type == 0:  # Circle
            for opt_name in ["target_number", "print_sequence"]:
                if opt_name in self.settings:
                    self.labels['settings'].remove(self.settings[opt_name]['row'])
                    del self.settings[opt_name]
            if "target_radius" not in self.settings:
                for option in self._config.get_configurable_options():
                    if "target_radius" in option:
                        self.add_option('settings', self.settings, 'target_radius', option["target_radius"])
                        break
        else:  # Unstructured (1)
            for opt_name in ["target_radius"]:
                if opt_name in self.settings:
                    self.labels['settings'].remove(self.settings[opt_name]['row'])
                    del self.settings[opt_name]
            for option in self._config.get_configurable_options():
                opt_name = list(option)[0]
                if opt_name in ["target_number", "print_sequence"] and opt_name not in self.settings:
                    self.add_option('settings', self.settings, opt_name, option[opt_name])
        
        self.labels['settings'].show_all()

    def activate(self):
        while len(self.menu) > 1:
            self.unload_menu()

    def back(self):
        if len(self.menu) > 1:
            self.unload_menu()
            return True
        return False

    def add_option(self, boxname, opt_array, opt_name, option):
        if option['type'] is None:
            return
        name = Gtk.Label()
        name.set_markup(f"<big><b>{option['name']}</b></big>")
        name.set_hexpand(True)
        name.set_vexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_valign(Gtk.Align.CENTER)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        labels.add(name)

        dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        dev.get_style_context().add_class("frame-item")
        dev.set_hexpand(True)
        dev.set_vexpand(False)
        dev.set_valign(Gtk.Align.CENTER)

        dev.add(labels)
        if option['type'] == "binary":
            switch = Gtk.Switch()
            is_active = self._config.get_config().getboolean(option['section'], opt_name)
            switch.set_active(is_active)
            
            if opt_name == "print_sequence":
                status_label = Gtk.Label()
                status_label.set_text(_("All at Once") if is_active else _("One at a Time"))
                # status_label.get_style_context().add_class("settings_menu")
                status_label.set_margin_start(10)
                
                def on_switch_changed(switch_widget, param):
                    status_label.set_text(_("All at Once") if switch_widget.get_active() else _("One at a Time"))
                    self.switch_config_option(switch_widget, param, option['section'], opt_name,
                                            option['callback'] if "callback" in option else None)
                
                switch.connect("notify::active", on_switch_changed)
                dev.add(status_label)
                dev.add(switch)
            else:
                switch.connect("notify::active", self.switch_config_option, option['section'], opt_name,
                               option['callback'] if "callback" in option else None)
                dev.add(switch)
        elif option['type'] == "dropdown":
            dropdown = Gtk.ComboBoxText()
            dropdown.get_style_context().add_class("custom-dropdown")
            for i, opt in enumerate(option['options']):
                dropdown.append(opt['value'], opt['name'])
                if opt['value'] == self._config.get_config()[option['section']].get(opt_name, option['value']):
                    dropdown.set_active(i)
            
            if opt_name == "detect_type":
                def on_detect_type_change(dropdown_widget):
                    new_value = dropdown_widget.get_active_id()
                    self._config.set(option['section'], opt_name, new_value)
                    self._config.save_user_config_options()
                    self.on_detect_type_changed(int(new_value))
                dropdown.connect("changed", on_detect_type_change)

            dropdown.connect("changed", self.on_dropdown_change, option['section'], opt_name,
                                option['callback'] if "callback" in option else None)
            dropdown.set_entry_text_column(0)
            dev.add(dropdown)
        elif option['type'] == "scale":
            dev.set_orientation(Gtk.Orientation.VERTICAL)
            scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.HORIZONTAL,
                                             min=option['range'][0], max=option['range'][1], step=option['step'])
            scale.set_hexpand(True)
            scale.set_value(int(self._config.get_config().get(option['section'], opt_name, fallback=option['value'])))
            scale.set_digits(0)
            scale.connect("button-release-event", self.scale_moved, option['section'], opt_name)
            dev.add(scale)
        elif option['type'] == "printer":
            box = Gtk.Box()
            box.set_vexpand(False)
            label = Gtk.Label(f"{option['moonraker_host']}:{option['moonraker_port']}")
            box.add(label)
            dev.add(box)
        elif option['type'] == "menu":
            open_menu = self._gtk.Button("settings", style="transparent", scale=1.2, image_margin = 0)
            open_menu.connect("clicked", self.load_menu, option['menu'], option['name'])
            open_menu.set_hexpand(False)
            open_menu.set_halign(Gtk.Align.END)
            dev.add(open_menu)
        elif option['type'] == "lang":
            select = self._gtk.Button("load", style="transparent", scale=1.2, image_margin = 0)
            select.connect("clicked", self._screen.change_language, option['name'])
            select.set_hexpand(False)
            select.set_halign(Gtk.Align.END)
            dev.add(select)
        elif option['type'] == "entry":
            current_value = self._config.get_config()[option['section']].get(opt_name, option.get('value', ''))
            entry_btn = self._gtk.Button(label=f"✎ {current_value}", style="transparent_more")
            entry_btn.set_halign(Gtk.Align.END)
            entry_btn.connect("clicked", self.show_numpad, option, opt_name, entry_btn)
            dev.add(entry_btn)

        opt_array[opt_name] = {
            "name": option['name'],
            "row": dev
        }

        priority_list = [
            "bed_center_calibration",
            "detect_type",
            "target_height",
            "target_radius",
            "target_number",
            "print_sequence",
            "purge_on_print_start", 
            "bed_mesh_on_print_start",
            "mesh_point",
            "purge_period"
        ]

        opts = sorted(list(opt_array), key=lambda x: (
            priority_list.index(x) if x in priority_list else len(priority_list),
            opt_array[x]['name'] 
        ))
        pos = opts.index(opt_name)

        self.labels[boxname].insert_row(pos)
        self.labels[boxname].attach(opt_array[opt_name]['row'], 0, pos, 1, 1)
        self.labels[boxname].show_all()

    def show_numpad(self, widget, option, opt_name, btn, device=None):
        current_value = self._config.get_config()[option['section']].get(opt_name, option.get('value', ''))
        menu_button = btn

        def save_and_close(text):
            if text is None or text is "":
                int_text = 0
            else:
                int_text = int(text)
            if int_text is None or int_text <= 0:
                int_text = 0
            if opt_name in ["target_height", "target_radius"]:
                if int_text > 100:
                    int_text = 100
                    self._screen.show_popup_message(_("Can't set above the maximum: %(int_text)s") % {"int_text": int_text})
            if opt_name == "target_number":
                if int_text > 10:
                    int_text = 10
                    self._screen.show_popup_message(_("Can't set above the maximum: %(int_text)s") % {"int_text": int_text})
            text = str(int_text)
            self._config.set(option['section'], opt_name, text)
            self._config.save_user_config_options()
            menu_button.set_label(f"✎ {text}")
            # logging.info(f"Saved {opt_name}: {text}")
            self._screen.remove_keyboard()
            self._gtk.remove_dialog(dialog)

            logging.debug(f"{opt_name} changed to {text}")
            gcode_command = f"SET_{opt_name.upper()}"
            self._screen._ws.klippy.gcode_script(f"{gcode_command} VALUE={text}")

        grid = Gtk.Grid()
        grid.get_style_context().add_class('numpad')
        grid.set_vexpand(True)
        grid.set_hexpand(True)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)

        dialog = self._gtk.Dialog(self._screen, [], grid, lambda d, r: self._gtk.remove_dialog(d),
                                 option, opt_name, btn)
        dialog.set_modal(False)
        dialog.get_style_context().add_class('numpad-dialog')

        def close_dialog_callback(widget):
            self._screen.remove_keyboard()
            self._gtk.remove_dialog(dialog)

        keys = [
            ['1', 'numpad_tleft'],
            ['2', 'numpad_top'],
            ['3', 'numpad_top'],
            ['4', 'numpad_top'],
            ['5', 'numpad_top'],
            ['B', 'numpad_tright'],
            ['6', 'numpad_bleft'],
            ['7', 'numpad_bottom'],
            ['8', 'numpad_bottom'],
            ['9', 'numpad_bottom'],
            ['0', 'numpad_bottom'],
            ['E', 'numpad_bright']
        ]
        
        self.labels["keypad"] = NumpadKeypad(self._screen, save_and_close, None, close_dialog_callback, columns=6, key_pattern=keys)
        self.labels["keypad"].clear()
        self.labels["keypad"].labels['entry'].set_text(current_value)
        self.labels["keypad"].set_halign(Gtk.Align.CENTER)
        self.labels["keypad"].set_valign(Gtk.Align.CENTER)

        grid.add(self.labels["keypad"])

        dialog.set_title(option['name'])
        dialog.set_position(Gtk.WindowPosition.CENTER)
        dialog.show_all()
