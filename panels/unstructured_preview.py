import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GdkPixbuf, Gtk, Pango

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kwargs):
    return UnstructuredPreviewPanel(*args, **kwargs)


class UnstructuredPreviewPanel(ScreenPanel):
    IMAGE_SIZE = 300

    def __init__(self, screen, title, preview=False):
        super().__init__(screen, title)
        self.preview = preview
        self.image_files = screen.get_cam_test_images()
        self.image_index = 0
        self.preview_state = {
            "camera_available": True,
            "detect_type": 1,
            "detection_state": "complete",
            "detection_error": "",
            "target_count": 3,
            "selected_target_ids": [1, 2, 3],
            "targets_ready": True,
            "print_sequence": 0,
            "targets": [
                {"id": 1, "pixel_x": 410.3, "pixel_y": 285.7, "x": 84.2, "y": 96.5,
                 "angle": -92.0, "selected": True},
                {"id": 2, "pixel_x": 622.8, "pixel_y": 302.1, "x": 132.4, "y": 101.2,
                 "angle": 1.5, "selected": True},
                {"id": 3, "pixel_x": 819.6, "pixel_y": 276.4, "x": 178.7, "y": 94.8,
                 "angle": 89.2, "selected": True},
            ],
        }
        self.selected_ids = set()
        self.default_selection_applied = False

        self.status = Gtk.Label()
        self.status.set_halign(Gtk.Align.END)
        self.status.set_hexpand(True)
        self.status.set_xalign(1.0)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_margin_start(4)
        self.status.set_margin_end(4)

        layout = Gtk.Grid()
        layout.set_column_spacing(8)
        layout.set_row_spacing(8)
        layout.set_margin_start(4)
        layout.set_margin_end(4)
        layout.set_margin_top(8)
        layout.set_margin_bottom(8)

        # Camera image viewer with the same navigation behavior as detect_type=0.
        overview = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.previous_button = self._gtk.Button("arrow_left", style="transparent_arrow", scale=1.0)
        self.previous_button.connect("clicked", self.previous_image)
        overview.pack_start(self.previous_button, False, False, 0)
        self.image_frame = Gtk.Frame()
        self.image_frame.set_size_request(self.IMAGE_SIZE, self.IMAGE_SIZE)
        overview.pack_start(self.image_frame, False, False, 0)
        self.next_button = self._gtk.Button("arrow_right", style="transparent_arrow", scale=1.0)
        self.next_button.connect("clicked", self.next_image)
        overview.pack_start(self.next_button, False, False, 0)
        layout.attach(overview, 0, 0, 1, 3)

        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.target_rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        target_scroll = self._gtk.ScrolledWindow()
        target_scroll.set_min_content_height(115)
        target_scroll.add(self.target_rows)
        details.pack_start(target_scroll, True, True, 0)

        self.sequence = Gtk.ComboBoxText()
        self.sequence.append("0", _("One at a Time"))
        self.sequence.append("1", _("All at Once"))
        self.sequence.connect("changed", self.sequence_changed)
        sequence_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sequence_label = Gtk.Label(label=_("Print Sequence"))
        sequence_label.set_halign(Gtk.Align.START)
        sequence_row.pack_start(sequence_label, False, False, 0)
        sequence_row.pack_start(self.sequence, False, False, 0)
        details.pack_start(sequence_row, False, False, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.set_halign(Gtk.Align.CENTER)
        self.ok_button = self._gtk.Button(None, _("OK"), "color2")
        self.ok_button.connect("clicked", self.accept_selection)
        self.ok_button.set_size_request(100, 34)
        self.ok_button.set_hexpand(False)
        self.ok_button.set_vexpand(False)
        actions.pack_start(self.ok_button, False, False, 0)
        self.cancel_button = self._gtk.Button(None, _("Cancel"), "color3")
        self.cancel_button.connect("clicked", self.cancel_selection)
        self.cancel_button.set_size_request(100, 34)
        self.cancel_button.set_hexpand(False)
        self.cancel_button.set_vexpand(False)
        actions.pack_start(self.cancel_button, False, False, 0)
        details.pack_start(actions, False, False, 0)
        layout.attach(details, 1, 0, 1, 3)

        self.content.pack_start(self.status, False, False, 4)
        self.content.pack_start(layout, True, True, 0)
        self.show_camera_image()
        self.refresh()

    def activate(self):
        if self.preview:
            self.refresh()
            return
        self._screen._ws.klippy.object_subscription(
            {"objects": {"bed_center_calibration": None}}, self.subscription_response
        )
        self.refresh()

    def subscription_response(self, response, _method, _params):
        if "error" in response:
            message = response["error"].get("message", str(response["error"]))
            self.status.set_text(message)
            logging.warning("Bed center calibration status is unavailable: %s", message)
            return
        status = response.get("result", {}).get("status", {})
        if status:
            self._printer.process_update(status)
            self.refresh()

    def process_update(self, action, data):
        if action == "notify_status_update" and "bed_center_calibration" in data:
            self.refresh()

    def _state(self):
        if self.preview:
            return self.preview_state
        return self._printer.get_stat("bed_center_calibration") or {}

    def _targets(self):
        return self._state().get("targets", []) or []

    def refresh(self):
        state = self._state()
        targets = self._targets()
        if not state:
            self.status.set_text(_("Waiting for bed center calibration status from Klipper."))
        else:
            camera = _("Camera available") if state.get("camera_available") else _("Camera unavailable")
            detection = state.get("detection_state", _("Unknown"))
            error = state.get("detection_error")
            details = [f"{_('Target Count')}: {state.get('target_count', len(targets))}"]
            # details = [camera, f"{_('Detection')}: {detection}",
            #             f"{_('Targets')}: {state.get('target_count', len(targets))}"]
            if error:
                details.append(f"{_('Error')}: {error}")
            self.status.set_text(" · ".join(details))

        selected = set(state.get("selected_target_ids", []))
        if not selected:
            selected = {target.get("id") for target in targets if target.get("selected")}
        if targets and not self.default_selection_applied:
            self.default_selection_applied = True
            if not selected:
                selected = {target.get("id") for target in targets}
                if self.preview:
                    self.preview_state["selected_target_ids"] = sorted(selected)
                    for target in targets:
                        target["selected"] = True
                else:
                    ids = ",".join(str(target_id) for target_id in sorted(selected))
                    self._send_gcode(f"BED_CENTER_SET_SELECTION TARGETS={ids}")
        self.selected_ids = selected

        for child in self.target_rows.get_children():
            self.target_rows.remove(child)
        for item in targets:
            target_id = item.get("id")
            row = Gtk.CheckButton(label=(
                f"#{target_id} ({item.get('x', 0):.2f}, {item.get('y', 0):.2f})\n"
                f"{_('Angle')}: {item.get('angle', 0):.1f}°"
            ))
            row.get_child().set_line_wrap(True)
            row.set_active(target_id in self.selected_ids)
            row.connect("toggled", self.target_toggled, target_id)
            row.set_tooltip_text(_("Selected") if target_id in self.selected_ids else _("Not selected"))
            self.target_rows.pack_start(row, False, False, 2)
        self.target_rows.show_all()

        sequence = state.get("print_sequence")
        if sequence is not None:
            self.sequence.handler_block_by_func(self.sequence_changed)
            self.sequence.set_active_id(str(int(sequence)))
            self.sequence.handler_unblock_by_func(self.sequence_changed)
        self.previous_button.set_sensitive(len(self.image_files) > 1)
        self.next_button.set_sensitive(len(self.image_files) > 1)

    def show_camera_image(self):
        for child in self.image_frame.get_children():
            self.image_frame.remove(child)
        if not self.image_files:
            self.image_frame.add(Gtk.Label(label=_("No captured images available")))
            self.image_frame.show_all()
            return

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.image_files[self.image_index])
            crop_x, crop_y = min(384, max(0, pixbuf.get_width() - 1)), min(158, max(0, pixbuf.get_height() - 1))
            crop_w = min(360, pixbuf.get_width() - crop_x)
            crop_h = min(352, pixbuf.get_height() - crop_y)
            cropped = pixbuf.new_subpixbuf(crop_x, crop_y, crop_w, crop_h)
            scaled = cropped.scale_simple(self.IMAGE_SIZE, self.IMAGE_SIZE, GdkPixbuf.InterpType.BILINEAR)
            self.image_frame.add(Gtk.Image.new_from_pixbuf(scaled))
        except Exception as error:
            logging.warning("Unable to load bed calibration image: %s", error)
            self.image_frame.add(Gtk.Label(label=_("Unable to load image")))
        self.image_frame.show_all()

    def previous_image(self, *_args):
        if self.image_files:
            self.image_index = (self.image_index - 1) % len(self.image_files)
            self.show_camera_image()

    def next_image(self, *_args):
        if self.image_files:
            self.image_index = (self.image_index + 1) % len(self.image_files)
            self.show_camera_image()

    def _send_gcode(self, script):
        if self.preview:
            return
        self._screen._ws.klippy.gcode_script(script, self.command_response)

    def accept_selection(self, *_args):
        if not self.selected_ids:
            self._screen.show_popup_message(_("Select at least one target."))
            return
        self._send_gcode("CAMCALIB_WAIT_DONE VALUE=True")

    def cancel_selection(self, *_args):
        if not self.preview:
            self._screen._ws.klippy.print_cancel(self.command_response)

    def command_response(self, response, method, params):
        if "error" in response:
            message = response["error"].get("message", str(response["error"]))
            self._screen.show_popup_message(message)
            logging.warning("Bed center calibration command failed: %s", message)

    def _set_selection(self, target_ids):
        if self.preview:
            self.preview_state["selected_target_ids"] = list(target_ids)
            for target in self.preview_state["targets"]:
                target["selected"] = target["id"] in target_ids
            self.refresh()
            return
        ids = ",".join(str(target_id) for target_id in target_ids)
        self._send_gcode(f"BED_CENTER_SET_SELECTION TARGETS={ids}")

    def target_toggled(self, button, target_id):
        selected = set(self.selected_ids)
        if button.get_active():
            selected.add(target_id)
        else:
            selected.discard(target_id)
        self._set_selection(sorted(selected))

    def sequence_changed(self, combo):
        value = combo.get_active_id()
        if value is not None:
            if self.preview:
                self.preview_state["print_sequence"] = int(value)
                return
            self._send_gcode(f"SET_PRINT_SEQUENCE ENABLE={value}")
