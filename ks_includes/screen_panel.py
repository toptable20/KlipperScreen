import logging
import datetime
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import os
import cv2
import numpy as np

class ScreenPanel:
    _screen = None
    _config = None
    _files = None
    _printer = None
    _gtk = None
    ks_printer_cfg = None

    def __init__(self, screen, title, **kwargs):
        self.menu = None
        ScreenPanel._screen = screen
        ScreenPanel._config = screen._config
        ScreenPanel._files = screen.files
        ScreenPanel._printer = screen.printer
        ScreenPanel._gtk = screen.gtk
        self.labels = {}
        self.control = {}
        self.title = title
        self.devices = {}
        self.active_heaters = []
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content.get_style_context().add_class("content")
        self.content.set_hexpand(True)
        self.content.set_vexpand(True)
        self._show_heater_power = self._config.get_main_config().getboolean('show_heater_power', False)
        self.bts = self._gtk.bsidescale

        self.update_dialog = None

    def _autoscroll(self, scroll, *args):
        adj = scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def emergency_stop(self, widget):
        if self._config.get_main_config().getboolean('confirm_estop', False):
            self._screen._confirm_send_action(widget, _("Are you sure you want to run Emergency Stop?"),
                                              "printer.emergency_stop")
        else:
            self._screen._ws.klippy.emergency_stop()

    def get_file_image(self, filename, width=None, height=None, small=False):
        if not self._files.has_thumbnail(filename):
            return None
        loc = self._files.get_thumbnail_location(filename, small)
        if loc is None:
            return None
        width = width if width is not None else self._gtk.img_width
        height = height if height is not None else self._gtk.img_height
        if loc[0] == "file":
            return self._gtk.PixbufFromFile(loc[1], width, height)
        if loc[0] == "http":
            return self._gtk.PixbufFromHttp(loc[1], width, height)
        return None

    def menu_item_clicked(self, widget, panel_type, item):
        if 'extra' in item:
            self._screen.show_panel(panel_type, item['panel'], item['name'], 1, False, extra=item['extra'])
            return
        self._screen.show_panel(panel_type, item['panel'], item['name'], 1, False)

    def load_menu(self, widget, name, title=None):
        logging.info(f"loading menu {name}")
        if f"{name}_menu" not in self.labels:
            logging.error(f"{name} not in labels")
            return

        for child in self.content.get_children():
            self.content.remove(child)

        self.menu.append(f'{name}_menu')
        self.content.add(self.labels[self.menu[-1]])
        self.content.show_all()
        if title:
            self._screen.base_panel.set_title(f"{self.title} | {title}")

    def unload_menu(self, widget=None):
        logging.debug(f"self.menu: {self.menu}")
        if len(self.menu) <= 1 or self.menu[-2] not in self.labels:
            return
        self._screen.base_panel.set_title(self._screen.panels[self._screen._cur_panels[-1]].title)
        self.menu.pop()
        for child in self.content.get_children():
            self.content.remove(child)
        self.content.add(self.labels[self.menu[-1]])
        self.content.show_all()

    def on_dropdown_change(self, combo, section, option, callback=None):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            value = model[tree_iter][1]
            logging.debug(f"[{section}] {option} changed to {value}")
            self._config.set(section, option, value)
            self._config.save_user_config_options()
            if callback is not None:
                callback(value)

    def scale_moved(self, widget, event, section, option):
        logging.debug(f"[{section}] {option} changed to {widget.get_value()}")
        if section not in self._config.get_config().sections():
            self._config.get_config().add_section(section)
        self._config.set(section, option, str(int(widget.get_value())))
        self._config.save_user_config_options()

    def switch_config_option(self, switch, gparam, section, option, callback=None):
        logging.debug(f"[{section}] {option} toggled {switch.get_active()}")
        if section not in self._config.get_config().sections():
            self._config.get_config().add_section(section)
        self._config.set(section, option, "True" if switch.get_active() else "False")
        self._config.save_user_config_options()

        if option == "bed_center_calibration":
            if self._config.get_main_config().getboolean("bed_center_calibration", False):  # Enabled
                self._screen._ws.klippy.gcode_script("SET_BED_CENTER_CALIBRATION ENABLE=1")
                
                self._config.camera_width = 1920
                self._config.camera_height = 1080
                x_p = 0.3
                y_p = 0.2
                w_p = 0.35
                h_p = 0.6

                self._config.camera_roi = (int(self._config.camera_width*x_p), int(self._config.camera_height*y_p), \
                                           int(self._config.camera_width*w_p), int(self._config.camera_height*h_p))  # x, y, w, h

                # Known calibration points for bed center calibration
                known_printer_points_mm = [
                    (130, 140), (95, 140), (130.50, 177),
                    (112, 160), (149, 160), (167, 141),
                    (151, 125), (130.5, 105), (115, 122)
                ]

                known_camera_points_px = [
                    (323.5, 180.5), (228.5, 183.5), (322.5, 80.5),
                    (273.5, 129.5), (373.5, 125.5), (422.5, 175.5),
                    (382.5, 223.5), (330.5, 279.5), (287.5, 233.5)
                ]
                np_camera_points = np.array(known_camera_points_px, dtype=np.float32)
                np_printer_points = np.array(known_printer_points_mm, dtype=np.float32)

                self._config.h_matrix, _ = cv2.findHomography(np_camera_points, np_printer_points)

                available_cameras = []
                max_devices = 5

                for i in range(max_devices):
                    device_path = f"/dev/video{i}"
                    if os.path.exists(device_path):
                        cap = cv2.VideoCapture(i)
                        if cap.isOpened():
                            available_cameras.append(i)
                            cap.release()
                
                self._config.available_cameras = available_cameras
                logging.info(f"Available cameras for bed center calibration: {self._config.available_cameras}")

            else:
                self._screen._ws.klippy.gcode_script("SET_BED_CENTER_CALIBRATION ENABLE=0")
                logging.info("Bed center calibration disabled.")

        if callback is not None:
            callback(switch.get_active())

    @staticmethod
    def format_time(seconds):
        if seconds is None or seconds <= 0:
            return "-"
        days = seconds // 86400
        seconds %= 86400
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{f'{days:2.0f}d ' if days > 0 else ''}" \
               f"{f'{hours:2.0f}h ' if hours > 0 else ''}" \
               f"{f'{minutes:2.0f}m ' if minutes > 0 else ''}" \
               f"{f'{seconds:2.0f}s' if days == 0 and hours == 0 and minutes == 0 else ''}"

    def format_eta(self, total, elapsed):
        if total is None:
            return "-"
        seconds = total - elapsed
        if seconds <= 0:
            return "-"
        days = seconds // 86400
        seconds %= 86400
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        eta = datetime.datetime.now() + datetime.timedelta(days=days, hours=hours, minutes=minutes)
        if self._config.get_main_config().getboolean("24htime", True):
            return f"{self.format_time(total - elapsed)} | {eta:%H:%M} {f' +{days:2.0f}d' if days > 0 else ''}"
        return f"{self.format_time(total - elapsed)} | {eta:%I:%M %p} {f' +{days:2.0f}d' if days > 0 else ''}"

    @staticmethod
    def format_size(size):
        size = float(size)
        suffixes = ["kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        for i, suffix in enumerate(suffixes, start=2):
            unit = 1024 ** i
            if size < unit:
                return f"{(1024 * size / unit):.1f} {suffix}"

    def update_temp(self, dev, temp, target, power, lines=1):
        if temp is None:
            return

        show_target = bool(target)
        if dev in self.devices and not self.devices[dev]["can_target"]:
            show_target = False

        show_power = show_target and self._show_heater_power and power is not None

        new_label_text = f"{int(temp):3}"
        if show_target:
            new_label_text += f"/{int(target)}"
        if dev not in self.devices:
            new_label_text += "°"
        if show_power:
            if lines == 2:
                # The label should wrap, but it doesn't work
                # this is a workaround
                new_label_text += "\n  "
            new_label_text += f" {int(power*100):3}%"

        if dev in self.labels:
            self.labels[dev].set_label(new_label_text)
        elif dev in self.devices:
            self.devices[dev]["temp"].get_child().set_label(new_label_text)
