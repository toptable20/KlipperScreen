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

        logging.info("init Replace panel")
        self._screen = screen
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.grid = Gtk.Grid()
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.header_label = Gtk.Label()
        self.main_label = Gtk.Label()
        self.sub_label = Gtk.Label()

        self.capacity_e_distance = { '25': 1805, '50':1485, '75': 1155, '100': 830 }
        # self.capacity_e_distance = { '25': 400, '50':300, '75': 200, '100': 100 }   # temp

        self.stack = Gtk.Stack()
    
        self.buttons = {
            'load': self._gtk.Button(label = _("Load"), style = "replace1"),
            'unload': self._gtk.Button(label = _("Unload"), style = "replace2"),

            'retry': self._gtk.Button(label = _("Retry"), style = "replace2"),
            'unlock_done': self._gtk.Button(label = _("Unlock Done"), style = "replace1"),
            'unload_done': self._gtk.Button(label = _("Unload Complete"), style = "replace1"),

            'load_ready': self._gtk.Button(label = _("Ready to load"), style = "replace1"),
            'add_extrude': self._gtk.Button(label = _("Extrude More"), style = "replace1"),
            'load_done': self._gtk.Button(label = _("Load Complete"), style = "replace2"),

            'capacity_25': self._gtk.Button(image_name = "25p", scale = 4),
            'capacity_50': self._gtk.Button(image_name = "50p", scale = 4),
            'capacity_75': self._gtk.Button(image_name = "75p", scale = 4),
            'capacity_100': self._gtk.Button(image_name = "100p", scale = 4),
        }

        self.header_box.get_style_context().add_class("header_box")
        self.header_label.set_halign(Gtk.Align.START)
        self.header_box.pack_start(self.header_label, False, False, 0)

        close_button = Gtk.Button(label="X")
        close_button.set_name("close_button")
        close_button.connect("clicked", self.update_mode, "initial")
        close_button.connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        self.header_box.pack_end(close_button, False, False, 0)
       
        self.main_label.set_justify(Gtk.Justification.CENTER)
        self.box.pack_start(self.main_label, False, False, 30)

        self.stack.add_named(self.initial_buttons(), "initial")
        self.stack.add_named(self.unload_1_buttons(), "unload_1")
        self.stack.add_named(self.unload_2_buttons(), "unload_2")
        self.stack.add_named(self.load_1_buttons(), "load_1")
        self.stack.add_named(self.load_2_buttons(), "load_2")
        self.stack.add_named(self.load_3_buttons(), "load_3")
        self.stack.set_homogeneous(False)

        self.box.pack_start(self.stack, False, False, 0)
        self.box.get_style_context().add_class("replace_panel")

        # self.update_mode(mode="init")
        GLib.idle_add(lambda: self.update_mode(mode="initial"))

        self.grid.attach(self.header_box, 0, 0, 1, 1)
        self.grid.attach(self.box, 0, 1, 1, 5)
        self.content.add(self.grid)

    def set_header_label(self, header_label):
        self.header_label.set_text(f"ⓘ {header_label}")

    def set_main_label(self, main_label):
        self.main_label.set_text(f"{main_label}")

    def update_mode(self, widget=None, mode='initial'):
        logging.info(f"mode: {mode}")

        self.stack.set_visible_child_name(mode)

        if mode == "initial":
            self.set_header_label(_("Replace Food Ink"))
            self.set_main_label(_("Do you want to replace the Food Ink?"))
            logging.info("mode initial")

        elif mode == "unload_1":
            self.set_header_label(_("STEP 1/2) Unload Food Ink"))
            self.set_main_label(_("Hold the top of the Food Ink extrusion rod,\nrotate clockwise \"90 degrees\" to unlock it."))
            logging.info("mode unload_1")

        elif mode == "unload_2":
            self.set_header_label(_("STEP 2/2) Unload Food Ink"))
            self.set_main_label(_("Please unload Food Ink."))
            logging.info("mode unload_2")

        elif mode == "load_1":
            self.set_header_label(_("STEP 1/3) Load Food Ink"))
            self.set_main_label(_("After loading the Food Ink, align the extrusion rod with the joint \n and rotate it \"90 degrees\" counterclockwise to lock it."))  
            self.wait_for_move_done()
            self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
            # 푸드잉크를 장착하고, 푸드잉크 압출 막대와 압출 막대 결합부를 반시계방향으로 "90도" 회전하여 잠금 상태로 만드십시오.
            logging.info("mode load_1")

        elif mode == "load_2":
            self.set_header_label(_("STEP 2/3) Load Food Ink"))
            self.set_main_label(_("Select the capacity of the Food Ink to load."))
            logging.info("mode load_2")

        elif mode == "load_3":
            self.set_header_label(_("STEP 3/3) Load Food Ink"))
            self.set_main_label(_("Observe the nozzle.\nIf Food Ink is extruded, select 'Load Complete'.\nIf not, select 'Extrude More'."))
            logging.info("mode load_3")
    
    def initial_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.sub_label.set_justify(Gtk.Justification.CENTER)
        self.sub_label.set_name("warning_label")
        self.sub_label.set_hexpand(False)
        self.sub_label.set_halign(Gtk.Align.CENTER)
        self.sub_label.set_text(_("Please operate the screen after the printer has stopped."))
        box.pack_start(self.sub_label, True, True, 0)

        self.buttons['load'].set_size_request(150, 80)
        self.buttons['load'].set_hexpand(False)
        self.buttons['load'].set_halign(Gtk.Align.CENTER)
        self.buttons['load'].connect("clicked", lambda w: logging.info("장착 버튼 클릭됨"))
        self.buttons['load'].connect("clicked", self.update_mode, "load_1")
        box.pack_start(self.buttons['load'], True, True, 30)

        self.buttons['unload'].set_size_request(150, 80)
        self.buttons['unload'].set_hexpand(False)
        self.buttons['unload'].set_halign(Gtk.Align.CENTER)
        self.buttons['unload'].connect("clicked", lambda w: logging.info("제거 버튼 클릭됨"))
        self.buttons['unload'].connect("clicked", self.update_mode, "unload_1")
        box.pack_start(self.buttons['unload'], True, True, 0)

        return box

    def unload_1_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.buttons['retry'].set_size_request(200, 80)
        self.buttons['retry'].connect("clicked", lambda w: logging.info("재시도"))
        self.buttons['retry'].connect("clicked", self.gcode_retry)
        box.pack_start(self.buttons['retry'], False, False, 0)

        self.buttons['unlock_done'].set_size_request(200, 80)
        self.buttons['unlock_done'].connect("clicked", lambda w: logging.info("잠금 해제 완료"))
        self.buttons['unlock_done'].connect("clicked", self.update_mode, "unload_2")
        box.pack_start(self.buttons['unlock_done'], False, False, 0)    

        return box
    
    def unload_2_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # box.set_name("replace_panel")

        self.buttons['unload_done'].set_size_request(150, 80)
        self.buttons['unload_done'].connect("clicked", lambda w: logging.info("완료"))
        self.buttons['unload_done'].connect("clicked", self.update_mode, "initial")
        self.buttons['unload_done'].connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        box.pack_start(self.buttons['unload_done'], False, False, 0)    

        return box
            
    def load_1_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.buttons['load_ready'].set_size_request(150, 80)
        self.buttons['load_ready'].set_hexpand(False)
        self.buttons['load_ready'].set_halign(Gtk.Align.CENTER)
        self.buttons['load_ready'].connect("clicked", lambda w: logging.info("장착 준비 완료"))
        self.buttons['load_ready'].connect("clicked", self.update_mode, "load_2")
        self.buttons['load_ready'].connect("clicked", self.gcode_load_before)
        box.pack_start(self.buttons['load_ready'], True, True, 50)

        return box

    def load_2_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # box.set_name("replace_panel")

        self.buttons['capacity_25'].connect("clicked", lambda w: logging.info("25%"))
        self.buttons['capacity_25'].connect("clicked", self.gcode_check_capacity, "25")
        self.buttons['capacity_50'].connect("clicked", lambda w: logging.info("50%"))
        self.buttons['capacity_50'].connect("clicked", self.gcode_check_capacity, "50")
        self.buttons['capacity_75'].connect("clicked", lambda w: logging.info("75%"))
        self.buttons['capacity_75'].connect("clicked", self.gcode_check_capacity, "75")
        self.buttons['capacity_100'].connect("clicked", lambda w: logging.info("100%"))
        self.buttons['capacity_100'].connect("clicked", self.gcode_check_capacity, "100")

        self.buttons['capacity_25'].connect("clicked", self.update_mode, "load_3")
        self.buttons['capacity_50'].connect("clicked", self.update_mode, "load_3")
        self.buttons['capacity_75'].connect("clicked", self.update_mode, "load_3")
        self.buttons['capacity_100'].connect("clicked", self.update_mode, "load_3")

        box.pack_start(self.buttons['capacity_25'], False, False, 0)    
        box.pack_start(self.buttons['capacity_50'], False, False, 0)    
        box.pack_start(self.buttons['capacity_75'], False, False, 0)    
        box.pack_start(self.buttons['capacity_100'], False, False, 0)    

        return box
    
    def load_3_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.buttons['add_extrude'].set_size_request(150, 80)
        self.buttons['add_extrude'].connect("clicked", lambda w: logging.info("추가 압출"))
        self.buttons['add_extrude'].connect("clicked", self.gcode_add_extrude)
        box.pack_start(self.buttons['add_extrude'], False, False, 0)

        self.buttons['load_done'].set_size_request(150, 80)
        self.buttons['load_done'].connect("clicked", lambda w: logging.info("장착 완료"))
        self.buttons['load_done'].connect("clicked", self.gcode_load_done)
        self.buttons['load_done'].connect("clicked", self.update_mode, "initial")
        self.buttons['load_done'].connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        box.pack_start(self.buttons['load_done'], False, False, 0)    

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
        self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
        self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)
        self._screen._ws.klippy.gcode_script("FOODINK_POS")
        self._screen._ws.klippy.gcode_script("G1 E555 F3000")

    def gcode_load_done(self, widget):
        self.wait_for_move_done()
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_REL)
        self._screen._ws.klippy.gcode_script(KlippyGcodes.extrude(20, 2000))
        self._screen._ws.klippy.gcode_script(KlippyGcodes.extrude(-20, 3000))
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_ABS)
        self._screen._ws.klippy.gcode_script("G92 E0")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)
        self._screen._ws.klippy.gcode_script("WIPE_SEQUENCE")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.extrude(10, 3000))
        self._screen._ws.klippy.gcode_script("G92 E0")

    def gcode_retry(self,widget):
        self.wait_for_move_done()
        self._screen._ws.klippy.gcode_script(KlippyGcodes.E_HOME)
        self._screen._ws.klippy.gcode_script(KlippyGcodes.HOME)
        self._screen._ws.klippy.gcode_script("FOODINK_POS")        

    def gcode_check_capacity(self, widget, capacity):
        self.wait_for_move_done()
        logging.info(f"Selected capacity: {capacity}")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_ABS)
        self._screen._ws.klippy.gcode_script(f"G1 E{self.capacity_e_distance[capacity]} F3000")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_REL)
        self._screen._ws.klippy.gcode_script("G1 E70 F2000")
        self._screen._ws.klippy.gcode_script("G92 E0")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.EXTRUDE_ABS)

    # set non sensitive buttons immediately
    def wait_for_move_done(self, widget=None):
        buttons = ("add_extrude", "retry", "load_done", 
                   "capacity_25", "capacity_50", "capacity_75", "capacity_100",
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
        
    def process_busy(self, busy):
        # buttons for sensitive
        buttons = ("add_extrude", "retry", "load_done", 
                   "capacity_25", "capacity_50", "capacity_75", "capacity_100",
                   "load_ready")
        for button in buttons:
            if button in self.buttons:
                self.buttons[button].set_sensitive(not busy)

    def back(self):
        logging.info("back in replacefoodink")
        self._screen.base_panel.hide_side_buttons(False)
        self.update_mode("initial")

        
    