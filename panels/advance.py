import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GdkPixbuf

from ks_includes.screen_panel import ScreenPanel
import logging
import os
import glob


def create_panel(*args):
    return AdvancePanel(*args)


class AdvancePanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        
        # 캠테스트 이미지 네비게이션 관련
        self.cam_images = []
        self.cam_current_index = 0
        self.cam_dialog = None

        printer = self._printer.get_printer_status_data()
        
        self.grid = Gtk.Grid()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        button_configs = [
            {"key": "autoleveling", "name": _("Auto\nLeveling"), "panel": "more", "icon": "auto_leveling", "scale": "2.0"},
            {"key": "inputshaper", "name": _("Input Shaper"), "panel": "input_shaper", "icon": "input_shaper", "scale": "2.0"},
            {"key": "zcalibrate", "name": _("Z Calibrate"), "panel": "zcalibrate", "icon": "z-farther", "scale": "2.0"},
            {"key": "camtest", "name": _("Cam Test"), "panel": "more", "icon": "auto_leveling", "scale": "2.0"},
        ]

        self.buttons = {}

        ps = self._printer.get_stat("print_stats")
        logging.info(f"ps: {ps}")
        remove_input_shaper = False
        remove_z_calibration = False
        if ps['available_input_shaper'] is False:
            remove_input_shaper = True
        if ps['available_z_calibration'] is False:
            remove_z_calibration = True

        for config in button_configs:
            key = config["key"]
            target_panel = config["panel"]
            display_name = config["name"]
            icon_name = config["icon"]
            scale = float(config["scale"])
            logging.info(f"key: {key}")

            if remove_input_shaper and key == "inputshaper":
                logging.info("skip input shaper")
                continue
            if remove_z_calibration and key == "zcalibrate":
                logging.info("skip z calibrate")
                continue

            button = self._gtk.Button(icon_name, display_name, "top_menu", scale=scale, lines=2)
            self.buttons[key] = button

            label = self._find_label_in_button(button)
            if label:
                label.set_use_markup(True)
                label.set_line_wrap(True)
                label.set_justify(Gtk.Justification.CENTER)
                label.set_max_width_chars(8)
                if key == "autoleveling":
                    label.set_line_wrap_mode(Pango.WrapMode.WORD)
                    label.set_ellipsize(Pango.EllipsizeMode.NONE)
                    label.set_max_width_chars(5)
                elif key == "inputshaper":
                    label.set_line_wrap_mode(Pango.WrapMode.WORD)
                    label.set_ellipsize(Pango.EllipsizeMode.NONE)
                    label.set_max_width_chars(5)
                elif key == "zcalibrate":
                    label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                    label.set_ellipsize(Pango.EllipsizeMode.NONE)
                    label.set_max_width_chars(8)
            
            button.set_size_request(158, 177)
            button.set_hexpand(False)
            button.set_halign(Gtk.Align.CENTER)
            button.set_valign(Gtk.Align.CENTER)
            
            try:
                panel_obj = self._screen.env.from_string(target_panel).render(printer)
                
                if key == "autoleveling":
                    button.connect("clicked", self.confirm_leveling)
                elif key == "camtest":
                    button.connect("clicked", self.camtest)
                else:
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
        # header_box.pack_end(home_button, False, False, 0)

        self.grid.attach(header_box, 0, 0, 1, 1)
        self.grid.attach(box, 0, 0, 1, 20)
        
        box.set_hexpand(True)
        box.set_vexpand(True)
        self.content.add(self.grid)

    def camtest(self, widget):
        """Display camera test images with navigation"""
        # 이미지 폴더 경로 설정
        cam_test_path = os.path.expanduser("~/printer_data/screenshot")
        
        # 이미지 크롭 설정
        CROP_WIDTH = 360
        CROP_HEIGHT = 352
        CROP_OFFSET_X = 384  # X 오프셋 (필요시 조정)
        CROP_OFFSET_Y = 158  # Y 오프셋 (필요시 조정)
        
        # 폴더 존재 확인
        if not os.path.exists(cam_test_path):
            self._show_error_dialog(_("Camera test folder not found at:") + f"\n{cam_test_path}")
            return
        
        # "_success" 포함된 PNG 파일 찾기 (최대 5개, 최신순)
        image_files = sorted(
            [f for f in glob.glob(os.path.join(cam_test_path, "*_success*.png"))],
            key=os.path.getmtime, reverse=True
        )[:5]  # 최대 5개만
        
        if not image_files:
            self._show_error_dialog(_("No _success image files found in:") + f"\n{cam_test_path}")
            return
        
        self.cam_images = image_files
        self.cam_current_index = 0
        
        self._show_cam_image(CROP_WIDTH, CROP_HEIGHT, CROP_OFFSET_X, CROP_OFFSET_Y)
    
    def _show_cam_image(self, crop_width, crop_height, crop_offset_x, crop_offset_y):
        """Display current camera image with navigation arrows"""
        if not self.cam_images or self.cam_current_index >= len(self.cam_images):
            return
        
        current_image = self.cam_images[self.cam_current_index]
        
        try:
            # 전체 이미지 로드
            full_pixbuf = GdkPixbuf.Pixbuf.new_from_file(current_image)
            
            img_width = full_pixbuf.get_width()
            img_height = full_pixbuf.get_height()
            logging.debug(f"Image {self.cam_current_index + 1}/{len(self.cam_images)}: {img_width}x{img_height}")
            
            # 오프셋과 크롭 크기 계산
            crop_x = max(0, min(crop_offset_x, img_width - crop_width))
            crop_y = max(0, min(crop_offset_y, img_height - crop_height))
            crop_w = min(crop_width, img_width - crop_x)
            crop_h = min(crop_height, img_height - crop_y)
            
            # 이미지 자르고 스케일
            cropped_pixbuf = full_pixbuf.new_subpixbuf(crop_x, crop_y, crop_w, crop_h)
            scaled_pixbuf = cropped_pixbuf.scale_simple(
                300, 300,
                GdkPixbuf.InterpType.BILINEAR
            )
            
            # 이미지 위젯
            image = Gtk.Image.new_from_pixbuf(scaled_pixbuf)
            
            # 텍스트 레이블
            text_label = Gtk.Label()
            text_label.set_markup(
                f"<small>{os.path.basename(current_image)}</small>"
            )
            text_label.set_line_wrap(True)
            text_label.set_halign(Gtk.Align.CENTER)
            text_label.set_margin_bottom(5)
            
            # 좌측 화살표 버튼
            left_btn = self._gtk.Button("arrow_left", "", style="transparent_arrow", scale=1.3)
            left_btn.set_halign(Gtk.Align.CENTER)
            left_btn.connect("clicked", self._cam_prev_image, crop_width, crop_height, crop_offset_x, crop_offset_y)
            if self.cam_current_index == 0:
                left_btn.set_sensitive(False)
            
            # 우측 화살표 버튼
            right_btn = self._gtk.Button("arrow_right", "", style="transparent_arrow", scale=1.3)
            right_btn.connect("clicked", self._cam_next_image, crop_width, crop_height, crop_offset_x, crop_offset_y)
            if self.cam_current_index >= len(self.cam_images) - 1:
                right_btn.set_sensitive(False)
            
            # 레이아웃 구성
            img_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            img_hbox.set_halign(Gtk.Align.CENTER)
            img_hbox.pack_start(left_btn, False, False, 0)
            img_hbox.pack_start(image, False, False, 0)
            img_hbox.pack_start(right_btn, False, False, 0)
            
            grid = Gtk.Grid()
            grid.set_vexpand(True)
            grid.set_hexpand(True)
            grid.set_halign(Gtk.Align.CENTER)
            grid.set_valign(Gtk.Align.CENTER)
            grid.set_row_spacing(5)
            grid.attach(text_label, 0, 0, 1, 1)
            grid.attach(img_hbox, 0, 1, 1, 1)
            
            # 버튼 설정
            buttons = [
                {"name": _("OK"), "response": Gtk.ResponseType.OK},
                {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL},
            ]
            
            # 기존 다이얼로그 닫기
            if self.cam_dialog is not None:
                self._gtk.remove_dialog(self.cam_dialog)
            
            # 다이얼로그 생성
            self.cam_dialog = self._gtk.Dialog(self._screen, buttons, grid, self.camtest_response, btn_style="transparent_job_status")
            self.cam_dialog.set_title(_("Camera Test"))
            action_area = self.cam_dialog.get_action_area()
            action_area.set_halign(Gtk.Align.CENTER)
            action_area.set_homogeneous(True)
            
            # # 버튼 크기 조정
            # for child in action_area.get_children():
            #     if isinstance(child, Gtk.Button):
            #         child.get_style_context().add_class("transparent_job_status")
            #         child.set_size_request(60, 40)
            
        except Exception as e:
            logging.error(f"Failed to load image: {e}")
            self._show_error_dialog(_("Failed to load image:") + f"\n{str(e)}")
    
    def _cam_prev_image(self, widget, crop_width, crop_height, crop_offset_x, crop_offset_y):
        """Show previous image"""
        if self.cam_current_index > 0:
            self.cam_current_index -= 1
            self._show_cam_image(crop_width, crop_height, crop_offset_x, crop_offset_y)
    
    def _cam_next_image(self, widget, crop_width, crop_height, crop_offset_x, crop_offset_y):
        """Show next image"""
        if self.cam_current_index < len(self.cam_images) - 1:
            self.cam_current_index += 1
            self._show_cam_image(crop_width, crop_height, crop_offset_x, crop_offset_y)
    
    def _show_error_dialog(self, message):
        """Show error dialog"""
        error_label = Gtk.Label()
        error_label.set_markup(message)
        error_label.set_line_wrap(True)
        error_label.set_halign(Gtk.Align.CENTER)
        error_label.set_vexpand(True)
        
        buttons = [
            {"name": _("OK"), "response": Gtk.ResponseType.OK},
        ]
        
        dialog = self._gtk.Dialog(self._screen, buttons, error_label, self.camtest_response)
        dialog.set_title(_("Camera Test"))
    
    def camtest_response(self, dialog, response_id):
        """Handle camera test dialog response"""
        self._gtk.remove_dialog(dialog)
        if self.cam_dialog == dialog:
            self.cam_dialog = None
        if response_id == Gtk.ResponseType.OK:
            logging.info("Camera test OK pressed")
        elif response_id == Gtk.ResponseType.CANCEL:
            logging.info("Camera test CANCEL pressed")
    def confirm_leveling(self, widget):

        buttons = [
            {"name": _("OK"), "response": Gtk.ResponseType.OK},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL},
        ]

        label = Gtk.Label()
        label.set_markup(_("Do you want to start auto leveling?"))
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        label.set_valign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        grid = Gtk.Grid()
        grid.set_vexpand(True)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)
        grid.add(label)

        dialog = self._gtk.Dialog(self._screen, buttons, grid, self.confirm_leveling_response)
        dialog.set_title(_("Print"))
        action_area = dialog.get_action_area()
        action_area.set_halign(Gtk.Align.CENTER)
        action_area.set_homogeneous(True)

    def confirm_leveling_response(self, dialog, response_id):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.CANCEL:
            return
    
        self._screen._ws.klippy.gcode_script("BED_MESH_CALIBRATE")
        
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
