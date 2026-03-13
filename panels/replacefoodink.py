import logging
import re

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GLib

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ReplacePanel(*args)

class ReplacePanel(ScreenPanel):

    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.waiting_for_purge = False
        self._screen = screen
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.finalize = False
        self.prev_loading_done = False

        self.grid = Gtk.Grid()
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.set_homogeneous(False)
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.header_label = Gtk.Label()
        self.header_label_empty = Gtk.Label()
        self.main_label_init = Gtk.Label()
        self.main_label = Gtk.Label()
        self.sub_label = Gtk.Label()

        # https://docs.google.com/presentation/d/1t8PgIbQLNwGcM1IFSkaJIT0A3NHdXnfd3AjXWeEc1GA/edit?slide=id.g372ef704f52_0_80#slide=id.g372ef704f52_0_80
        self.capacity_e_distance = { '25': 1805, '50':1485, '75': 1155, '100': 830 }

        self.stack = Gtk.Stack()
    
        self.buttons = {
            'load': self._gtk.Button(label = _("Insert"), style = "replace1"),
            'unload': self._gtk.Button(label = _("Remove"), style = "replace2"),

            'retry': self._gtk.Button(label = _("Retry"), style = "replace2"),
            'unlock_done': self._gtk.Button(label = _("Unlock Done"), style = "replace1"),
            'unload_done': self._gtk.Button(label = _("Unload Complete"), style = "replace1"),

            'load_ready': self._gtk.Button(label = _("Ready to load"), style = "replace1"),
            'add_extrude': self._gtk.Button(label = _("Extrude Again"), style = "replace1"),
            'load_done': self._gtk.Button(label = _("Complete"), style = "replace2"),

            'set_temp_load2': self._gtk.Button(label = _("Set Temperature"), style = "settemp"),
            'set_temp_load3': self._gtk.Button(label = _("Set Temperature"), style = "settemp"),                                                           
        }

        self.header_box.get_style_context().add_class("header_box")
        self.header_label.set_halign(Gtk.Align.START)
        self.header_box.pack_start(self.header_label_empty, False, False, 0)
        self.header_box.pack_start(self.header_label, False, False, 0)

        self.main_label.set_justify(Gtk.Justification.CENTER)
        self.main_label_init.set_justify(Gtk.Justification.CENTER)
        self.box.pack_start(self.main_label_init, False, False, 0)
        self.box.pack_start(self.main_label, False, False, 0)

        self.stack.add_named(self.initial_buttons(), "initial")
        self.stack.add_named(self.unload_1_buttons(), "unload_1")
        self.stack.add_named(self.unload_2_buttons(), "unload_2")
        self.stack.add_named(self.load_1_buttons(), "load_1")
        self.stack.add_named(self.load_2_buttons(), "load_2")
        self.stack.set_homogeneous(False)

        self.box.pack_start(self.stack, False, False, 0)
        self.box.get_style_context().add_class("header_box_init")

        GLib.idle_add(lambda: self.update_mode(mode="initial"))

        self.grid.attach(self.header_box, 0, 0, 1, 1)
        self.grid.attach(self.box, 0, 1, 1, 6)
        self.content.add(self.grid)

    def set_header_label(self, header_label):
        self.header_label.set_text(f"ⓘ {header_label}")

    def set_main_label(self, main_label):
        self.main_label.set_text(f"{main_label}")

    def toggle_style(self, type):
        context = self.box.get_style_context()
        if type is 1:
            context.remove_class("header_box_normal")
            context.add_class("header_box_init")
        else:
            context.remove_class("header_box_init")
            context.add_class("header_box_normal")

    def activate(self):
        self.toggle_style(1)

    def update_mode(self, widget=None, mode='initial'):
        if mode is not "finalize":
            self.stack.set_visible_child_name(mode)

        if mode == "initial":
            self.set_header_label(_("Replace FoodInk"))
            self.toggle_style(1)
            self.set_main_label(_("Do you want to replace the FoodInk?"))
            # logging.info("mode initial")

        elif mode == "unload_1":
            self.set_header_label(_("STEP 1/2) Unload FoodInk"))
            self.toggle_style(0)
            self.set_main_label(_("Hold the top of the FoodInk extrusion rod,\nrotate clockwise \"90 degrees\" to unlock it."))
            self.wait_for_move_done()
            self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
            self._screen._ws.klippy.gcode_script("G92 E150")
            # logging.info("mode unload_1")

        elif mode == "unload_2":
            self.set_header_label(_("STEP 2/2) Unload FoodInk"))
            self.set_main_label(_("Please unload FoodInk."))
            # logging.info("mode unload_2")

        elif mode == "load_1":
            self.set_header_label(_("STEP 1/2) Load FoodInk"))
            self.toggle_style(0)
            self.set_main_label(_("After loading the FoodInk,\nalign the extrusion rod with the joint \n and rotate it \"90 degrees\" counterclockwise to lock it.\nSet temperature if preheating is needed before extrusion."))  
            self.wait_for_move_done()
            self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
            self._screen._ws.klippy.gcode_script("G92 E150")
            # 푸드잉크를 장착하고, 푸드잉크 압출 막대와 압출 막대 결합부를 반시계방향으로 "90도" 회전하여 잠금 상태로 만드십시오.
            # logging.info("mode load_1")

        elif mode == "load_2":
            self.set_header_label(_("STEP 2/2) Load FoodInk"))
            self.set_main_label(_("After the printer stops, observe the nozzle.\nIf FoodInk is extruded, select 'Load Complete'.\nIf not, select 'Extrude More'."))
            # logging.info("mode load_3")

        elif mode == "finalize":
            self.finalize = True
            # self.toggle_style(1) 
            # logging.info("mode finalize")
    
    def initial_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.sub_label.set_justify(Gtk.Justification.CENTER)
        self.sub_label.set_name("warning_label")
        self.sub_label.set_hexpand(False)
        self.sub_label.set_halign(Gtk.Align.CENTER)
        self.sub_label.set_text(_("Please operate the screen after the printer has stopped."))
        box.pack_start(self.sub_label, False, False, 0)

        button_configs = [
            {"key": "load", "nextmode": "load_1", "padding": 10},
            {"key": "unload", "nextmode": "unload_1", "padding": 0}
        ]

        for config in button_configs:
            button = self.buttons[config["key"]]
            button.set_size_request(150, 80)
            button.set_hexpand(False)
            button.set_halign(Gtk.Align.CENTER)
            button.connect("clicked", self.update_mode, config["nextmode"])
            box.pack_start(button, False, False, config["padding"])

        return box

    def unload_1_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.buttons['retry'].set_size_request(200, 80)
        self.buttons['retry'].connect("clicked", self.gcode_retry)
        box.pack_start(self.buttons['retry'], False, False, 0)

        self.buttons['unlock_done'].set_size_request(200, 80)
        self.buttons['unlock_done'].connect("clicked", self.update_mode, "unload_2")
        box.pack_start(self.buttons['unlock_done'], False, False, 0)    

        return box
    
    def unload_2_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.buttons['unload_done'].set_size_request(150, 80)
        self.buttons['unload_done'].connect("clicked", self.update_mode, "initial")
        self.buttons['unload_done'].connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        box.pack_start(self.buttons['unload_done'], False, False, 0)

        return box
            
    def load_1_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.buttons['load_ready'].set_size_request(150, 80)
        self.buttons['load_ready'].set_hexpand(False)
        self.buttons['load_ready'].set_halign(Gtk.Align.CENTER)
        self.buttons['load_ready'].connect("clicked", self.update_mode, "load_2")
        self.buttons['load_ready'].connect("clicked", self.gcode_load_before)
        box.pack_start(self.buttons['load_ready'], False, False, 50)

        return box

    def load_2_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.buttons['set_temp_load3'].set_size_request(100, 50)
        self.buttons['set_temp_load3'].connect("clicked", self.menu_item_clicked, "temperature", 
                                         {"panel": "temperature", "name": _("Temperature")})
        hbox1.pack_start(self.buttons['set_temp_load3'], False, False, 0)

        self.buttons['add_extrude'].set_size_request(150, 80)
        self.buttons['add_extrude'].connect("clicked", self.gcode_add_extrude)
        hbox2.pack_start(self.buttons['add_extrude'], False, False, 0)

        self.buttons['load_done'].set_size_request(150, 80)
        self.buttons['load_done'].connect("clicked", self.gcode_load_done)
        self.buttons['load_done'].connect("clicked", self.update_mode, "finalize")
        hbox2.pack_start(self.buttons['load_done'], False, False, 0)

        box.pack_start(hbox1, False, False, 0)
        box.pack_start(hbox2, False, False, 0)

        return box
    
    def gcode_add_extrude(self, widget):
        self.wait_for_move_done()
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_REL)
        self._screen._ws.klippy.gcode_script(KlippyGcodes.extrude(25, 3000))
        self._screen._ws.klippy.gcode_script(KlippyGcodes.extrude(25, 2000))
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_ABS)
        self._screen._ws.klippy.gcode_script("G92 E0")

    def gcode_load_before(self, widget):
        self.wait_for_move_done()
        # self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
        self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)
        # self._screen._ws.klippy.gcode_script("FOODINK_POS")
        self._screen._ws.klippy.gcode_script("G1 X-100 Y205 Z35 F6000")
        self._screen._ws.klippy.gcode_script("G1 E555 F3000")
        self.gcode_purge_detect()
        

    def gcode_purge_detect(self, widget=None):
        self.wait_for_move_done()
        self._screen._ws.klippy.gcode_script("PURGE_LOADING")
        self.waiting_for_purge = True

    def gcode_load_done(self, widget):
        self.wait_for_move_done()
        self._screen._ws.klippy.gcode_script("WIPE_SEQUENCE")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.extrude(10, 3000))
        self._screen._ws.klippy.gcode_script("G92 E0")

    def gcode_retry(self,widget):
        self.wait_for_move_done()
        self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
        self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)
        self._screen._ws.klippy.gcode_script("FOODINK_POS")        

    # set non sensitive buttons immediately
    def wait_for_move_done(self, widget=None):
        buttons = ("add_extrude", "retry", "load_done", 
                   "load_ready")
        for button in buttons:
            if button in self.buttons:
                self.buttons[button].set_sensitive(False)

    def process_update(self, action, data):
        if action == "notify_busy":
            self.process_busy(data)
            return
        if action != "notify_status_update" or self._screen.printer is None:
            return
        if self.waiting_for_purge:
            ps = self._printer.get_stat("purge_sensing")
            if ps['loading_done'] is True and self.prev_loading_done is False:
                if ps['is_detect'] is True:
                    self.waiting_for_purge = False
                    # logging.info("Purge detected")
                else: # ps['is_detect'] is False:
                    self.waiting_for_purge = False
                    # logging.info("No purge detected")
                    self._screen.show_popup_message(_("Purge not detected."))

            self.prev_loading_done = ps['loading_done']
        
    def process_busy(self, busy):
        # buttons for sensitive
        buttons = ("load", "unload", "add_extrude", "retry", "load_done", 
                   "load_ready")
        for button in buttons:
            if button in self.buttons:
                self.buttons[button].set_sensitive(not busy)

        if self.finalize and not busy:
            self.finalize = False
            self.update_mode("initial")
            self._screen._menu_go_back(home=True)

    def back(self):
        # logging.info("back in replacefoodink")
        self._screen.base_panel.hide_side_buttons(False)
        self.update_mode("initial")

        
    
