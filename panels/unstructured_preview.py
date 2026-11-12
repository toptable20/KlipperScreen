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
        self.image_crop = None
        self.image_source_size = None
        self.image_widget = None
        self.subscription_active = False
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
        self.showing_detection_error = False

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
        self.image_overlay = Gtk.Overlay()
        self.image_labels = Gtk.DrawingArea()
        self.image_labels.set_size_request(self.IMAGE_SIZE, self.IMAGE_SIZE)
        self.image_labels.set_hexpand(True)
        self.image_labels.set_vexpand(True)
        self.image_labels.connect("draw", self.draw_target_ids)
        self.image_overlay.add_overlay(self.image_labels)
        self.image_overlay.set_overlay_pass_through(self.image_labels, True)
        self.image_frame.add(self.image_overlay)
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
        objects = dict(self._screen.ws_subscription["objects"])
        objects["bed_center_calibration"] = None
        self.subscription_active = True
        self._screen._ws.klippy.object_subscription(
            {"objects": objects}, self.subscription_response
        )
        self.refresh()

    def deactivate(self):
        if self.preview or not self.subscription_active:
            return
        self.subscription_active = False
        self._screen._ws.klippy.object_subscription(
            self._screen.ws_subscription, self.subscription_response
        )

    def subscription_response(self, response, _method, _params):
        if "error" in response:
            message = response["error"].get("message", str(response["error"]))
            self.status.set_text(message)
            logging.warning("Bed center calibration status is unavailable: %s", message)
            if self.subscription_active:
                self.subscription_active = False
                self._screen._ws.klippy.object_subscription(
                    self._screen.ws_subscription
                )
            return
        status = response.get("result", {}).get("status", {})
        if status:
            if "exclude_object" in status:
                exclude_status = status["exclude_object"]
                if exclude_status is None or (
                    isinstance(exclude_status, dict)
                    and exclude_status
                    and all(value is None for value in exclude_status.values())
                ):
                    status = dict(status)
                    status.pop("exclude_object", None)
            self._printer.process_update(status)
            self._screen.process_update("notify_status_update", status)
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
        detection_failed = state.get("detection_state") == "error"
        self.ok_button.set_sensitive(not detection_failed)
        if detection_failed != self.showing_detection_error:
            self.showing_detection_error = detection_failed
            self.show_camera_image()

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
        self.image_labels.queue_draw()

        sequence = state.get("print_sequence")
        if sequence is not None:
            self.sequence.handler_block_by_func(self.sequence_changed)
            self.sequence.set_active_id(str(int(sequence)))
            self.sequence.handler_unblock_by_func(self.sequence_changed)
        self.previous_button.set_sensitive(len(self.image_files) > 1)
        self.next_button.set_sensitive(len(self.image_files) > 1)

    def show_camera_image(self):
        if self.image_widget is not None:
            self.image_overlay.remove(self.image_widget)
            self.image_widget = None
        if self.showing_detection_error:
            message = _("Detection failed")
            error = self._state().get("detection_error")
            if error:
                message = f"{message}\n{error}"
            self.image_crop = None
            self.image_widget = Gtk.Label(label=message)
            self.image_widget.set_line_wrap(True)
            self.image_widget.set_justify(Gtk.Justification.CENTER)
            self.image_widget.set_halign(Gtk.Align.CENTER)
            self.image_widget.set_valign(Gtk.Align.CENTER)
            self.image_overlay.add(self.image_widget)
            self.image_frame.show_all()
            self.image_labels.queue_draw()
            return
        if not self.image_files:
            self.image_widget = Gtk.Label(label=_("No captured images available"))
            self.image_overlay.add(self.image_widget)
            self.image_frame.show_all()
            return

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.image_files[self.image_index])
            x_ratio, y_ratio, width_ratio, height_ratio = self._screen.CAMERA_CROP
            image_width = pixbuf.get_width()
            image_height = pixbuf.get_height()
            crop_w = max(1, min(round(image_width * width_ratio), image_width))
            crop_h = max(1, min(round(image_height * height_ratio), image_height))
            crop_x = max(0, min(round(image_width * x_ratio), image_width - crop_w))
            crop_y = max(0, min(round(image_height * y_ratio), image_height - crop_h))
            cropped = pixbuf.new_subpixbuf(crop_x, crop_y, crop_w, crop_h)
            cropped = cropped.rotate_simple(GdkPixbuf.PixbufRotation.UPSIDEDOWN)
            scaled = cropped.scale_simple(self.IMAGE_SIZE, self.IMAGE_SIZE, GdkPixbuf.InterpType.BILINEAR)
            self.image_crop = (crop_x, crop_y, crop_w, crop_h)
            self.image_source_size = (image_width, image_height)
            self.image_widget = Gtk.Image.new_from_pixbuf(scaled)
            self.image_overlay.add(self.image_widget)
        except Exception as error:
            logging.warning("Unable to load bed calibration image: %s", error)
            self.image_crop = None
            self.image_source_size = None
            self.image_widget = Gtk.Label(label=_("Unable to load image"))
            self.image_overlay.add(self.image_widget)
        self.image_frame.show_all()
        self.image_labels.queue_draw()

    def draw_target_ids(self, _widget, context):
        if not self.image_crop:
            return False

        allocation = self.image_labels.get_allocation()
        width, height = allocation.width, allocation.height
        if width <= 0 or height <= 0:
            return False
        crop_x, crop_y, crop_width, crop_height = self.image_crop
        scale_x, scale_y = width / crop_width, height / crop_height

        context.select_font_face("Sans", 0, 1)
        context.set_font_size(18)
        context.set_line_width(3.5)
        context.set_line_join(1)
        for target in self._targets():
            try:
                x = width - 1 - (float(target["pixel_x"]) - crop_x) * scale_x
                y = height - 1 - (float(target["pixel_y"]) - crop_y) * scale_y
                label = f"#{target['id']}"
            except (KeyError, TypeError, ValueError):
                continue
            if not (0 <= x <= width and 0 <= y <= height):
                continue
            extents = context.text_extents(label)
            text_width = extents[2]
            text_height = extents[3]
            context.move_to(x - text_width / 2 - extents[0], y + text_height / 2)
            context.text_path(label)
            context.set_source_rgb(0, 0, 0)
            context.stroke_preserve()
            context.set_source_rgb(1, 1, 1)
            context.fill()
        return False

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
        selected_ids = ",".join(str(target_id) for target_id in sorted(self.selected_ids))
        print_sequence = self.sequence.get_active_id()
        if print_sequence is None:
            print_sequence = str(self._state().get("print_sequence", 0))
        self._send_gcode(
            f"BED_CENTER_SET_SELECTION TARGETS={selected_ids}\n"
            f"SET_PRINT_SEQUENCE ENABLE={print_sequence}\n"
            "CAMCALIB_WAIT_DONE VALUE=True"
        )

    def cancel_selection(self, *_args):
        self._screen._ws.klippy.print_cancel(self._screen.camcalib_cancel_response)
        self._screen._menu_go_back()

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
