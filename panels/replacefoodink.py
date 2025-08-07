import logging
import re

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ReplacePanel(*args)

class ReplacePanel(ScreenPanel):

    def __init__(self, screen, title):
        super().__init__(screen, title)

        logging.info("init Replace panel")
        self._screen = screen
        self.grid = self._gtk.HomogeneousGrid()
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=50, halign=Gtk.Align.CENTER)
        self.header_label = Gtk.Label()
        self.main_label = Gtk.Label()

        self.stack = Gtk.Stack()
    
        self.buttons = {
            'load': self._gtk.Button(label = _("Load"), style = "replace1"),
            'unload': self._gtk.Button(label = _("Unload"), style = "replace2"),

            'retry': self._gtk.Button(label = _("Retry"), style = "replace1"),
            'unload_done': self._gtk.Button(label = _("Unload_Done"), style = "replace2"),
            'finish': self._gtk.Button(label = _("Finish"), style = "replace1"),

            'add_extrude': self._gtk.Button(label = _("Add_Extrude"), style = "replace1"),
            'capacity_25': self._gtk.Button("arrow-right"),
            'capacity_50': self._gtk.Button("arrow-right"),
            'capacity_75': self._gtk.Button("arrow-right"),
            'capacity_100': self._gtk.Button("arrow-right"),
        }

        self.header_box.set_name("header_box")
        self.header_label.set_halign(Gtk.Align.START)
        self.header_box.pack_start(self.header_label, False, False, 0)

        close_button = Gtk.Button(label="X")
        close_button.set_name("close_button")
        close_button.connect("clicked", self.update_mode, "init")
        close_button.connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        self.header_box.pack_end(close_button, False, False, 0)
       
        # self.box.set_name("replace_panel")

        # self.main_label = Gtk.Label(label=_("Do you want to replace the Food ink?"))
        
        self.main_label.set_name("replace_panel")
        self.main_label.set_justify(Gtk.Justification.CENTER)
        self.box.pack_start(self.main_label, False, False, 30)

        self.stack.add_named(self.initial_buttons(), "initial")
        self.stack.add_named(self.second_buttons(), "second")
        self.stack.add_named(self.third_buttons(), "third")

        self.box.pack_start(self.stack, False, False, 0)

        self.update_mode("init")

        self.grid.attach(self.header_box, 0, 0, 1, 1)
        self.grid.attach(self.box, 0, 1, 1, 5)
        self.content.add(self.grid)

    def set_header_label(self, header_label):
        self.header_label.set_text(f"ⓘ {header_label}")

    def set_main_label(self, main_label):
        self.main_label.set_text(f"{main_label}")

    def update_mode(self, widget, mode='init'):
        if mode == "init":
            self.set_header_label(_("Replace Food Ink"))
            self.set_main_label(_("Do you want to replace the Food ink?"))
            self.stack.set_visible_child_name("initial")
            logging.info("mode init")

        elif mode == "second":
            self.set_header_label(_("STEP 1/2) Unload Food Ink"))
            self.set_main_label(_("Hold the top of the Food Ink extrusion rod,\nrotate clockwise \"90 degrees\" to unlock it."))
            self.stack.set_visible_child_name("second")
            logging.info("mode second")

        elif mode == "third":
            self.set_header_label(_("STEP 2/2) Unload Food Ink"))
            self.set_main_label(_("Please unload Food Ink"))
            self.stack.set_visible_child_name("third")
            logging.info("mode third")
    
    def initial_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_name("replace_panel")

        self.buttons['load'].set_size_request(150, 80)
        self.buttons['load'].connect("clicked", lambda w: logging.info("삽입 버튼 클릭됨"))
        # self.buttons['load'].connect("clicked", self.press_load)
        box.pack_start(self.buttons['load'], False, False, 0)        

        self.buttons['unload'].set_size_request(150, 80)
        self.buttons['unload'].connect("clicked", lambda w: logging.info("제거 버튼 클릭됨"))
        self.buttons['unload'].connect("clicked", self.update_mode, "second")
        box.pack_start(self.buttons['unload'], False, False, 0)

        return box

    def second_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.set_name("replace_panel")

        self.buttons['retry'].set_size_request(150, 80)
        self.buttons['retry'].connect("clicked", lambda w: logging.info("재시도"))
        box.pack_start(self.buttons['retry'], False, False, 0)    

        self.buttons['unload_done'].set_size_request(150, 80)
        self.buttons['unload_done'].connect("clicked", lambda w: logging.info("잠금 해제 완료"))
        self.buttons['unload_done'].connect("clicked", self.update_mode, "third")
        box.pack_start(self.buttons['unload_done'], False, False, 0)    

        return box
    
    def third_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.set_name("replace_panel")

        self.buttons['finish'].set_size_request(150, 80)
        self.buttons['finish'].connect("clicked", lambda w: logging.info("완료"))
        self.buttons['finish'].connect("clicked", self.update_mode, "init")
        self.buttons['finish'].connect("clicked", lambda w: self._screen._menu_go_back(home=True))
        box.pack_start(self.buttons['finish'], False, False, 0)    

        return box
    
    def press_load(self, widget):
        self.set_header_label("aaaa")

        self.content.show_all()

    def process_update(self, action, data):
        if action == "notify_busy":
            self.process_busy(data)
            return
        if action != "notify_status_update" or self._screen.printer is None:
            return
        
    def process_busy(self, busy):
        for button in self.buttons:
            self.buttons[button].set_sensitive((not busy))

    def back(self):
        logging.info("back in replacefoodink")
        self.update_mode("init")

        
    