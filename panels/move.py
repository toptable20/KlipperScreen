import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return MovePanel(*args)


class MovePanel(ScreenPanel):
    distances = ['0.1', '0.5', '1', '5', '10', '25', '50']
    distance = distances[-2]

    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.settings = {}
        self.menu = ['move_menu']
        img_scale = 1.8
        img_margin = 20
        self.buttons = {
            'x+': self._gtk.Button("x_plus", "X+", "basic", img_scale, image_margin=img_margin),
            'x-': self._gtk.Button("x_minus", "X-", "basic", img_scale, image_margin=img_margin),
            'y+': self._gtk.Button("y_plus", "Y+", "basic", img_scale, image_margin=img_margin),
            'y-': self._gtk.Button("y_minus", "Y-", "basic", img_scale, image_margin=img_margin),
            'z+': self._gtk.Button("z_plus", "Z+", "basic", img_scale, image_margin=img_margin),
            'z-': self._gtk.Button("z_minus", "Z-", "basic", img_scale, image_margin=img_margin),
            'home': self._gtk.Button("homeall", _("Home All"), "basic", img_scale, image_margin=img_margin),
        }
        self.buttons['x+'].connect("clicked", self.move, "X", "+")
        self.buttons['x-'].connect("clicked", self.move, "X", "-")
        self.buttons['y+'].connect("clicked", self.move, "Y", "+")
        self.buttons['y-'].connect("clicked", self.move, "Y", "-")
        self.buttons['z+'].connect("clicked", self.move, "Z", "+")
        self.buttons['z-'].connect("clicked", self.move, "Z", "-")
        self.buttons['home'].connect("clicked", self.home)
        
        for button in self.buttons:
            btn = self.buttons[button]
            btn.set_size_request(120, 125)
            btn.set_hexpand(False)
            btn.set_vexpand(False)
            btn.set_halign(Gtk.Align.CENTER)
            btn.set_valign(Gtk.Align.CENTER)

        grid = self._gtk.HomogeneousGrid()
        grid.set_hexpand(True)
        grid.set_halign(Gtk.Align.CENTER)
        # grid.set_row_homogeneous(True)
        # grid.set_column_homogeneous(True)
        grid.set_column_spacing(10) 
        grid.set_row_spacing(5)

        if self._screen.vertical_mode:
            if self._screen.lang_ltr:
                grid.attach(self.buttons['x+'], 2, 1, 1, 1)
                grid.attach(self.buttons['x-'], 0, 1, 1, 1)
                grid.attach(self.buttons['z+'], 2, 2, 1, 1)
                grid.attach(self.buttons['z-'], 0, 2, 1, 1)
            else:
                grid.attach(self.buttons['x+'], 0, 1, 1, 1)
                grid.attach(self.buttons['x-'], 2, 1, 1, 1)
                grid.attach(self.buttons['z+'], 0, 2, 1, 1)
                grid.attach(self.buttons['z-'], 2, 2, 1, 1)
            grid.attach(self.buttons['y+'], 1, 0, 1, 1)
            grid.attach(self.buttons['y-'], 1, 1, 1, 1)

        else:
            if self._screen.lang_ltr:
                grid.attach(self.buttons['x+'], 1, 0, 1, 1)
                grid.attach(self.buttons['x-'], 1, 1, 1, 1)
            else:
                grid.attach(self.buttons['x+'], 0, 1, 1, 1)
                grid.attach(self.buttons['x-'], 2, 1, 1, 1)
            grid.attach(self.buttons['y+'], 2, 0, 1, 1)
            grid.attach(self.buttons['y-'], 2, 1, 1, 1)
            grid.attach(self.buttons['z+'], 3, 0, 1, 1)
            grid.attach(self.buttons['z-'], 3, 1, 1, 1)

        grid.attach(self.buttons['home'], 0, 0, 1, 1)

        distgrid = Gtk.Grid()
        distgrid.set_column_homogeneous(True)
        for j, i in enumerate(self.distances):
            self.labels[i] = self._gtk.Button(label=i)
            self.labels[i].set_direction(Gtk.TextDirection.LTR)
            self.labels[i].connect("clicked", self.change_distance, i)
            ctx = self.labels[i].get_style_context()
            if (self._screen.lang_ltr and j == 0) or (not self._screen.lang_ltr and j == len(self.distances) - 1):
                ctx.add_class("distbutton_top")
                logging.info("top")
            elif (not self._screen.lang_ltr and j == 0) or (self._screen.lang_ltr and j == len(self.distances) - 1):
                ctx.add_class("distbutton_bottom")
                logging.info("bot")
            else:
                ctx.add_class("distbutton")
                logging.info("mid")
            if i == self.distance:
                ctx.add_class("distbutton_active")
                logging.info("atv")
            distgrid.attach(self.labels[i], j, 0, 1, 1)

        for p in ('pos_x', 'pos_y', 'pos_z'):
            self.labels[p] = Gtk.Label()
        self.labels['move_dist'] = Gtk.Label(_("Move Distance (mm)"))
        self.labels['move_dist'].get_style_context().add_class("changesub")

        posbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        posbox.pack_start(self.labels['pos_x'], True, True, 0)
        posbox.pack_start(self.labels['pos_y'], True, True, 0)
        posbox.pack_start(self.labels['pos_z'], True, True, 0)
        posbox.set_valign(Gtk.Align.CENTER)
        posbox.set_halign(Gtk.Align.CENTER)
        grid.attach(posbox, 0, 1, 1, 1)

        bottomgrid = self._gtk.HomogeneousGrid()
        bottomgrid.set_direction(Gtk.TextDirection.LTR)
        bottomgrid.attach(self.labels['move_dist'], 0, 0, 1, 1)

        spacer_right = Gtk.Button()
        spacer_right.get_style_context().add_class("transparent_spacer")
        spacer_right.set_vexpand(True)

        movebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        movebox.set_hexpand(False)
        movebox.set_size_request(640, -1)
        movebox.pack_start(grid, False, False, 0)
        movebox.pack_start(bottomgrid, False, False, 0)
        movebox.pack_start(distgrid, False, False, 0)

        # bottomgrid.set_halign(Gtk.Align.CENTER)
        # distgrid.set_halign(Gtk.Align.CENTER)
        # distgrid.set_hexpand(True)

        self.labels['move_menu'] = self._gtk.HomogeneousGrid()
        self.labels['move_menu'].set_row_homogeneous(False)
        self.labels['move_menu'].set_column_homogeneous(False)
        self.labels['move_menu'].set_halign(Gtk.Align.CENTER)
        self.labels['move_menu'].attach(movebox, 0, 0, 1, 1)
        # self.labels['move_menu'].attach(bottomgrid, 0, 1, 1, 1)
        # self.labels['move_menu'].attach(distgrid, 0, 2, 1, 1)
        # self.labels['move_menu'].attach(spacer_right, 1, 0, 1, 1)

        self.content.add(self.labels['move_menu'])

    def process_busy(self, busy):
        buttons = ("home")
        for button in buttons:
            if button in self.buttons:
                self.buttons[button].set_sensitive(not busy)

    def process_update(self, action, data):
        if action == "notify_busy":
            self.process_busy(data)
            return
        if action != "notify_status_update":
            return
        homed_axes = self._printer.get_stat("toolhead", "homed_axes")
        if homed_axes == "xyz":
            if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                self.labels['pos_x'].set_text(f"X: {data['gcode_move']['gcode_position'][0]:.2f}")
                self.labels['pos_y'].set_text(f"Y: {data['gcode_move']['gcode_position'][1]:.2f}")
                self.labels['pos_z'].set_text(f"Z: {data['gcode_move']['gcode_position'][2]:.2f}")
        else:
            if "x" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_x'].set_text(f"X: {data['gcode_move']['gcode_position'][0]:.2f}")
            else:
                self.labels['pos_x'].set_text("X: ?")
            if "y" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_y'].set_text(f"Y: {data['gcode_move']['gcode_position'][1]:.2f}")
            else:
                self.labels['pos_y'].set_text("Y: ?")
            if "z" in homed_axes:
                if "gcode_move" in data and "gcode_position" in data["gcode_move"]:
                    self.labels['pos_z'].set_text(f"Z: {data['gcode_move']['gcode_position'][2]:.2f}")
            else:
                self.labels['pos_z'].set_text("Z: ?")

    def change_distance(self, widget, distance):
        logging.info(f"### Distance {distance}")
        self.labels[f"{self.distance}"].get_style_context().remove_class("distbutton_active")
        self.labels[f"{distance}"].get_style_context().add_class("distbutton_active")
        self.distance = distance

    def move(self, widget, axis, direction):
        if self._config.get_config()['main'].getboolean(f"invert_{axis.lower()}", False):
            direction = "-" if direction == "+" else "+"

        dist = f"{direction}{self.distance}"
        config_key = "move_speed_z" if axis == "Z" else "move_speed_xy"
        speed = None if self.ks_printer_cfg is None else self.ks_printer_cfg.getint(config_key, None)
        if speed is None:
            speed = self._config.get_config()['main'].getint(config_key, 20)
        speed = 60 * max(1, speed)

        self._screen._ws.klippy.gcode_script(f"{KlippyGcodes.MOVE_RELATIVE}\n{KlippyGcodes.MOVE} {axis}{dist} F{speed}")
        if self._printer.get_stat("gcode_move", "absolute_coordinates"):
            self._screen._ws.klippy.gcode_script("G90")

    def add_option(self, boxname, opt_array, opt_name, option):
        name = Gtk.Label()
        name.set_markup(f"<big><b>{option['name']}</b></big>")
        name.set_hexpand(True)
        name.set_vexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_valign(Gtk.Align.CENTER)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        dev.get_style_context().add_class("frame-item")
        dev.set_hexpand(True)
        dev.set_vexpand(False)
        dev.set_valign(Gtk.Align.CENTER)
        dev.add(name)

        if option['type'] == "binary":
            box = Gtk.Box()
            box.set_vexpand(False)
            switch = Gtk.Switch()
            switch.set_hexpand(False)
            switch.set_vexpand(False)
            switch.set_active(self._config.get_config().getboolean(option['section'], opt_name))
            switch.connect("notify::active", self.switch_config_option, option['section'], opt_name)
            switch.set_property("width-request", round(self._gtk.font_size * 7))
            switch.set_property("height-request", round(self._gtk.font_size * 3.5))
            box.add(switch)
            dev.add(box)
        elif option['type'] == "scale":
            dev.set_orientation(Gtk.Orientation.VERTICAL)
            scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.HORIZONTAL,
                                             min=option['range'][0], max=option['range'][1], step=option['step'])
            scale.set_hexpand(True)
            scale.set_value(int(self._config.get_config().get(option['section'], opt_name, fallback=option['value'])))
            scale.set_digits(0)
            scale.connect("button-release-event", self.scale_moved, option['section'], opt_name)
            dev.add(scale)

        opt_array[opt_name] = {
            "name": option['name'],
            "row": dev
        }

        opts = sorted(list(opt_array), key=lambda x: opt_array[x]['name'])
        pos = opts.index(opt_name)

        self.labels[boxname].insert_row(pos)
        self.labels[boxname].attach(opt_array[opt_name]['row'], 0, pos, 1, 1)
        self.labels[boxname].show_all()

    def back(self):
        if len(self.menu) > 1:
            self.unload_menu()
            return True
        return False

    def home(self, widget):
        self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)

        # if "delta" in self._printer.get_config_section("printer")['kinematics']:
        #     self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)
        #     return
        # name = "homing"
        # disname = self._screen._config.get_menu_name("move", name)
        # menuitems = self._screen._config.get_menu_items("move", name)
        # self._screen.show_panel(name, "menu", disname, 1, False, items=menuitems)
