import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from panels.menu import MenuPanel

from ks_includes.widgets.heatergraph import HeaterGraph
from ks_includes.widgets.keypad import Keypad

import threading
import time

def create_panel(*args, **kwargs):
    return MainPanel(*args, **kwargs)


class MainPanel(MenuPanel):
    def __init__(self, screen, title, items=None):
        super().__init__(screen, title, items)
        self.graph_retry_timeout = None
        self.left_panel = None
        self.devices = {}
        self.graph_update = None
        self.active_heater = None
        self.h = self.f = 0
        self.main_menu = self._gtk.HomogeneousGrid()
        self.main_menu.set_hexpand(True)
        self.main_menu.set_vexpand(True)
        self.graph_retry = 0
        scroll = self._gtk.ScrolledWindow()

        monitor = Gdk.Display.get_default().get_primary_monitor()
        self.width = self._config.get_main_config().getint("width", monitor.get_geometry().width)
        self.height = self._config.get_main_config().getint("height", monitor.get_geometry().height)

        logging.info("### Making MainMenu")

        stats = self._printer.get_printer_status_data()["printer"]
        if stats["temperature_devices"]["count"] > 0 or stats["extruders"]["count"] > 0:
            self._gtk.reset_temp_color()
            self.main_menu.attach(self.create_left_panel(), 0, 0, 1, 1)
        if self._screen.vertical_mode:
            self.labels['menu'] = self.arrangeMenuItems(items, 3, True)
            scroll.add(self.labels['menu'])
            self.main_menu.attach(scroll, 0, 1, 1, 1)
        else:
            self.labels['menu'] = self.arrangeMenuItems(items, 2, True)
            # for i, child in enumerate(self.labels['menu'].get_children(), start=1):
            #     if child.get_label() in ("Replace Food Ink", "푸드잉크 교체"):
            #         child.connect("clicked", self.replace_foodink)                    
                
            scroll.add(self.labels['menu'])
            self.main_menu.attach(scroll, 1, 0, 1, 1)
        self.content.add(self.main_menu)

        filament_sensors = self._printer.get_filament_sensors()
        limit = 5
        if len(filament_sensors) > 0:
            for s, x in enumerate(filament_sensors):
                if s > limit:
                    break
                name = x[23:].strip()
                self.labels[x] = {
                    'label': Gtk.Label(name.capitalize().replace('_', ' ')),
                    'switch': Gtk.Switch(),
                    'box': Gtk.Box()
                }
                self.labels[x]['label'].set_halign(Gtk.Align.CENTER)
                self.labels[x]['label'].set_hexpand(True)
                # self.labels[x]['label'].set_ellipsize(Pango.EllipsizeMode.END)
                self.labels[x]['switch'].set_property("width-request", round(self._gtk.font_size * 2))
                self.labels[x]['switch'].set_property("height-request", round(self._gtk.font_size))
                # self.labels[x]['switch'].connect("notify::active", None, name, x)
                self.labels[x]['box'].pack_start(self.labels[x]['label'], True, True, 10)
                self.labels[x]['box'].pack_start(self.labels[x]['switch'], False, False, 0)
                self.labels[x]['box'].get_style_context().add_class("filament_sensor")

        self.sensor_check_thread = None
        self.sensor_stop_flag = False
        self.sensor_detected = False

        self.extruder_check_thread = None
        self.exturder_running = False

        self.extruder_period = 0.1
        self.temp_sensor_data = []

    def extruder_loop_negative(self):
        self.exturder_running = True
        self.sensor_detected = False

        self.sensor_wait()

        self._screen._ws.klippy.gcode_script("G91 E0", logger=False)

        for _ in range(500):
            if self.sensor_detected:
                self._screen._ws.klippy.gcode_script("M84")
                self._screen._ws.klippy.gcode_script("G92 E0")
                self._screen._ws.klippy.gcode_script("G1 E25 F1500")
                self._screen._ws.klippy.gcode_script("G1 E5 F1500")
                self._screen._ws.klippy.gcode_script("M400")
                logging.info("Motion stopped by sensor.")
                break
            
            self._screen._ws.klippy.gcode_script("G1 E-2 F15000", logger=False)
            time.sleep(self.extruder_period)

        self.exturder_running = False
        self.sensor_stop_flag = True
        logging.info("extruder_loop_negative done")

    def extruder_wait_negative(self):
        if self.extruder_check_thread and self.extruder_check_thread.is_alive():
            return
        
        logging.info("start extruder thread")

        self.sensor_stop_flag = False
        self.extruder_check_thread = threading.Thread(target = self.extruder_loop_negative)
        self.extruder_check_thread.daemon = True
        self.extruder_check_thread.start()

    def sensor_done(self):
        self.sensor_stop_flag = True

    def sensor_loop(self):
        logging.info("start sensor loop")
        while not self.sensor_stop_flag:
            try:
                for x in self._printer.get_filament_sensors():
                    if x in self.temp_sensor_data:
                        if 'enabled' in self.temp_sensor_data[x]:
                            self._printer.set_dev_stat(x, "enabled", self.temp_sensor_data[x]['enabled'])
                        if 'filament_detected' in self.temp_sensor_data[x]:
                            self._printer.set_dev_stat(x, "filament_detected", self.temp_sensor_data[x]['filament_detected'])
                        
                            if self._printer.get_stat(x, "enabled"):
                                if self.temp_sensor_data[x]['filament_detected']:
                                    self.sensor_detected = True
                                else:
                                    self.sensor_detected = False
                if self.sensor_detected:
                    logging.info("sensor checked")
                    break
            except Exception as e:
                logging.info("wrong sensor")
            
            time.sleep(0.05)

    def sensor_wait(self):
        if self.sensor_check_thread and self.sensor_check_thread.is_alive():
            return
        
        logging.info("start sensing thread")
        
        self.sensor_stop_flag = False
        self.sensor_check_thread = threading.Thread(target=self.sensor_loop)
        self.sensor_check_thread.daemon = True
        self.sensor_check_thread.start()

    def process_busy(self, busy):
        for button in self.buttons:
            if button == "temperature":
                continue
            self.buttons[button].set_sensitive((not busy))

    def replace_foodink(self, widget):
        # buttons = [
        #     {"name": _("Continue"), "response": Gtk.ResponseType.OK},
        #     {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        # ]

        # # 다이얼로그 생성
        # dialog = Gtk.Dialog(
        #     title="푸드잉크 교체",
        #     transient_for=self._screen,
        # )
        # dialog.set_default_size(self._screen.width, self._screen.height)
        # dialog.set_modal(True)
        # dialog.set_resizable(False)
        # dialog.set_decorated(True)

        # content_area = dialog.get_content_area()

        # box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        # content_area.pack_start(box, True, True, 0)

        # header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # header_box.set_name("header_box")
        # header_box.set_hexpand(True)

        # header_label = Gtk.Label(label=_("ⓘ Replace Food Ink"))
        # header_label.set_name("header_label")
        # header_label.set_halign(Gtk.Align.START)
        # header_box.pack_start(header_label, False, False, 0)

        # close_button = Gtk.Button(label="X")
        # close_button.set_name("close_button")
        # close_button.connect("clicked", lambda w: dialog.destroy())
        # header_box.pack_end(close_button, False, False, 0)

        # box.pack_start(header_box, False, False, 0)

        # label = Gtk.Label(label=_("Do you want to replace the Food ink?"))
        # label.set_name("foodink_label")
        # label.set_justify(Gtk.Justification.CENTER)
        # box.pack_start(label, False, False, 30)

        # button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=50, halign=Gtk.Align.CENTER)
        # box.pack_start(button_box, False, False, 40)

        # load_button = Gtk.Button(label=_("Load"))
        # load_button.set_name("load_button")
        # load_button.set_size_request(150, 80)
        # load_button.connect("clicked", lambda w: logging.info("삽입 버튼 클릭됨"))  # 기능 구현 필요
        # button_box.pack_start(load_button, False, False, 0)

        # unload_button = Gtk.Button(label=_("Unload"))
        # unload_button.set_name("unload_button")
        # unload_button.set_size_request(150, 80)
        # unload_button.connect("clicked", lambda w: logging.info("제거 버튼 클릭됨"))    # 기능 구현 필요
        # button_box.pack_start(unload_button, False, False, 0)

        # content_area.pack_start(box, False, False, 0)

        # dialog.get_style_context().add_class("foodink_dialog")

        # dialog.show_all()
        
        # if self._screen.show_cursor:
        #     dialog.get_window().set_cursor(
        #         Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.ARROW))
        # else:
        #     dialog.get_window().set_cursor(
        #         Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.BLANK_CURSOR))

        # self._screen.dialogs.append(dialog)
        logging.info(f"Showing dialog {dialog}")

        # if direction == "-":
        #     self.extruder_wait_negative()
        # if direction == "+":
        #     if not self.load_filament:
        #         self._screen.show_popup_message("Macro LOAD_FILAMENT not found")
        #     else:
        #         self._screen._ws.klippy.gcode_script(f"LOAD_FILAMENT SPEED={self.speed * 60}")
        #         logging.info("send LOAD_FILAMENT done")

    def update_graph_visibility(self):
        if self.left_panel is None or not self._printer.get_temp_store_devices():
            if self._printer.get_temp_store_devices():
                logging.info("Retrying to create left panel")
                self._gtk.reset_temp_color()
                self.main_menu.attach(self.create_left_panel(), 0, 0, 1, 1)
            self.graph_retry += 1
            if self.graph_retry < 5:
                if self.graph_retry_timeout is None:
                    self.graph_retry_timeout = GLib.timeout_add_seconds(5, self.update_graph_visibility)
            else:
                logging.debug(f"Could not create graph {self.left_panel} {self._printer.get_temp_store_devices()}")
            return False
        count = 0
        for device in self.devices:
            visible = self._config.get_config().getboolean(f"graph {self._screen.connected_printer}",
                                                           device, fallback=True)
            self.devices[device]['visible'] = visible
            self.labels['da'].set_showing(device, visible)
            if visible:
                count += 1
                self.devices[device]['name'].get_style_context().add_class(self.devices[device]['class'])
                self.devices[device]['name'].get_style_context().remove_class("graph_label_hidden")
            else:
                self.devices[device]['name'].get_style_context().add_class("graph_label_hidden")
                self.devices[device]['name'].get_style_context().remove_class(self.devices[device]['class'])
        if count > 0:
            if self.labels['da'] not in self.left_panel:
                self.left_panel.add(self.labels['da'])
            self.labels['da'].queue_draw()
            self.labels['da'].show()
            if self.graph_update is None:
                # This has a high impact on load
                self.graph_update = GLib.timeout_add_seconds(5, self.update_graph)
        elif self.labels['da'] in self.left_panel:
            self.left_panel.remove(self.labels['da'])
            if self.graph_update is not None:
                GLib.source_remove(self.graph_update)
                self.graph_update = None
        self.graph_retry = 0
        return False

    def activate(self):
        self.update_graph_visibility()
        self._screen.base_panel_show_all()

    def deactivate(self):
        if self.graph_update is not None:
            GLib.source_remove(self.graph_update)
            self.graph_update = None
        if self.graph_retry_timeout is not None:
            GLib.source_remove(self.graph_retry_timeout)
            self.graph_retry_timeout = None
        if self.active_heater is not None:
            self.hide_numpad()

    def add_device(self, device):

        logging.info(f"Adding device: {device}")

        temperature = self._printer.get_dev_stat(device, "temperature")
        if temperature is None:
            return False

        devname = device.split()[1] if len(device.split()) > 1 else device
        # Support for hiding devices by name
        if devname.startswith("_"):
            return False

        if device.startswith("extruder"):
            if self._printer.extrudercount > 1:
                image = f"extruder-{device[8:]}" if device[8:] else "extruder-0"
            else:
                image = "extruder"
            class_name = f"graph_label_{device}"
            dev_type = "extruder"
        elif device == "heater_bed":
            image = "bed"
            devname = "Heater Bed"
            class_name = "graph_label_heater_bed"
            dev_type = "bed"
        elif device.startswith("heater_generic"):
            self.h += 1
            image = "heater"
            class_name = f"graph_label_sensor_{self.h}"
            dev_type = "sensor"
        elif device.startswith("temperature_fan"):
            self.f += 1
            image = "fan"
            class_name = f"graph_label_fan_{self.f}"
            dev_type = "fan"
        elif self._config.get_main_config().getboolean("only_heaters", False):
            return False
        else:
            self.h += 1
            image = "heat-up"
            class_name = f"graph_label_sensor_{self.h}"
            dev_type = "sensor"

        rgb = self._gtk.get_temp_color(dev_type)

        can_target = self._printer.device_has_target(device)
        logging.debug(f"{device} has target? : {can_target}")
        self.labels['da'].add_object(device, "temperatures", rgb, False, True)
        if can_target:
            self.labels['da'].add_object(device, "targets", rgb, True, False)

        # name = self._gtk.Button(image, devname.capitalize().replace("_", " "), None, self.bts, Gtk.PositionType.LEFT, 1)
        name = self._gtk.Button(image, _("Food Ink"), None, self.bts, Gtk.PositionType.LEFT, 1)
        name.connect("clicked", self.toggle_visibility, device)
        name.set_alignment(0, .5)
        visible = self._config.get_config().getboolean(f"graph {self._screen.connected_printer}", device, fallback=True)
        if visible:
            name.get_style_context().add_class(class_name)
        else:
            name.get_style_context().add_class("graph_label_hidden")
        self.labels['da'].set_showing(device, visible)

        temp = self._gtk.Button(label="", lines=1)
        if can_target:
            temp.connect("clicked", self.show_numpad, device)

        self.devices[device] = {
            "class": class_name,
            "name": name,
            "temp": temp,
            "can_target": can_target,
            "visible": visible
        }

        devices = sorted(self.devices)
        pos = devices.index(device) + 1

        self.labels['devices'].insert_row(pos)
        self.labels['devices'].attach(name, 0, pos, 1, 1)
        self.labels['devices'].attach(temp, 1, pos, 1, 1)
        self.labels['devices'].show_all()
        return True

    def toggle_visibility(self, widget, device):
        self.devices[device]['visible'] ^= True
        logging.info(f"Graph show {self.devices[device]['visible']}: {device}")

        section = f"graph {self._screen.connected_printer}"
        if section not in self._config.get_config().sections():
            self._config.get_config().add_section(section)
        self._config.set(section, f"{device}", f"{self.devices[device]['visible']}")
        self._config.save_user_config_options()

        self.update_graph_visibility()

    def change_target_temp(self, temp):
        name = self.active_heater.split()[1] if len(self.active_heater.split()) > 1 else self.active_heater
        temp = self.verify_max_temp(temp)
        if temp is False:
            return

        if self.active_heater.startswith('extruder'):
            self._screen._ws.klippy.set_tool_temp(self._printer.get_tool_number(self.active_heater), temp)
        elif self.active_heater == "heater_bed":
            self._screen._ws.klippy.set_bed_temp(temp)
        elif self.active_heater.startswith('heater_generic '):
            self._screen._ws.klippy.set_heater_temp(name, temp)
        elif self.active_heater.startswith('temperature_fan '):
            self._screen._ws.klippy.set_temp_fan_temp(name, temp)
        else:
            logging.info(f"Unknown heater: {self.active_heater}")
            self._screen.show_popup_message(_("Unknown Heater") + " " + self.active_heater)
        self._printer.set_dev_stat(self.active_heater, "target", temp)

    def verify_max_temp(self, temp):
        temp = int(temp)
        max_temp = int(float(self._printer.get_config_section(self.active_heater)['max_temp']))
        logging.debug(f"{temp}/{max_temp}")
        if temp > max_temp:
            self._screen.show_popup_message(_("Can't set above the maximum:") + f' {max_temp}')
            return False
        return max(temp, 0)

    def pid_calibrate(self, temp):
        if self.verify_max_temp(temp):
            script = {"script": f"PID_CALIBRATE HEATER={self.active_heater} TARGET={temp}"}
            self._screen._confirm_send_action(
                None,
                _("Initiate a PID calibration for:") + f" {self.active_heater} @ {temp} ºC"
                + "\n\n" + _("It may take more than 5 minutes depending on the heater power."),
                "printer.gcode.script",
                script
            )

    def create_left_panel(self):

        self.labels['devices'] = Gtk.Grid()
        self.labels['devices'].get_style_context().add_class('heater-grid')
        self.labels['devices'].set_vexpand(False)

        name = Gtk.Label(label="")
        temp = Gtk.Label(_("Temp (°C)"))
        temp.get_style_context().add_class("heater-grid-temp")

        self.labels['devices'].attach(name, 0, 0, 1, 1)
        self.labels['devices'].attach(temp, 1, 0, 1, 1)

        self.labels['da'] = HeaterGraph(self._printer, self._gtk.font_size)
        self.labels['da'].set_vexpand(True)

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.labels['devices'])

        self.left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.left_panel.add(scroll)

        for d in (self._printer.get_tools() + self._printer.get_heaters()):
            self.add_device(d)

        return self.left_panel

    def hide_numpad(self, widget=None):
        self.devices[self.active_heater]['name'].get_style_context().remove_class("button_active")
        self.active_heater = None

        if self._screen.vertical_mode:
            self.main_menu.remove_row(1)
            self.main_menu.attach(self.labels['menu'], 0, 1, 1, 1)
        else:
            self.main_menu.remove_column(1)
            self.main_menu.attach(self.labels['menu'], 1, 0, 1, 1)
        self.main_menu.show_all()

    def process_update(self, action, data):
        if action != "notify_status_update":
            return
        self.temp_sensor_data = data
        for x in (self._printer.get_tools() + self._printer.get_heaters()):
            self.update_temp(
                x,
                self._printer.get_dev_stat(x, "temperature"),
                self._printer.get_dev_stat(x, "target"),
                self._printer.get_dev_stat(x, "power"),
            )

        for x in self._printer.get_filament_sensors():
            if x in data:
                if 'enabled' in data[x]:
                    self._printer.set_dev_stat(x, "enabled", data[x]['enabled'])
                    self.labels[x]['switch'].set_active(data[x]['enabled'])
                if 'filament_detected' in data[x]:
                    self._printer.set_dev_stat(x, "filament_detected", data[x]['filament_detected'])
                    if self._printer.get_stat(x, "enabled"):
                        if data[x]['filament_detected']:
                            self.sensor_detected = True
                        else:
                            self.sensor_detected = False
                logging.info(f"{x}: {self._printer.get_stat(x)['filament_detected']}")

        return False

    def show_numpad(self, widget, device):

        if self.active_heater is not None:
            self.devices[self.active_heater]['name'].get_style_context().remove_class("button_active")
        self.active_heater = device
        self.devices[self.active_heater]['name'].get_style_context().add_class("button_active")

        if "keypad" not in self.labels:
            self.labels["keypad"] = Keypad(self._screen, self.change_target_temp, self.pid_calibrate, self.hide_numpad)
        can_pid = self._printer.state not in ["printing", "paused"] \
            and self._screen.printer.config[self.active_heater]['control'] == 'pid'
        self.labels["keypad"].show_pid(can_pid)
        self.labels["keypad"].clear()

        if self._screen.vertical_mode:
            self.main_menu.remove_row(1)
            self.main_menu.attach(self.labels["keypad"], 0, 1, 1, 1)
        else:
            self.main_menu.remove_column(1)
            self.main_menu.attach(self.labels["keypad"], 1, 0, 1, 1)
        self.main_menu.show_all()

    def update_graph(self):
        self.labels['da'].queue_draw()
        return True
