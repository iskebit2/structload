import io
import logging

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp, sp

from data.defaults import proje_data
from loads.snow_load import SnowLoad
from loads.spectrum import Spectrum
from windcalc.wind_results import WindReport

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

FONT = {
    "section": 16,
    "heading": 15,
    "body": 14,
    "table": 12,
    "small": 11,
}

# ----------------------------------------------------
# TEMA VE RENK PALETİ
# ----------------------------------------------------
THEME = {
    "bg_app": (0.08, 0.09, 0.11, 1),        # Çok Koyu Antrasit
    "bg_card": (0.13, 0.15, 0.19, 1),       # Koyu Kart Gri
    "bg_header": (0.18, 0.22, 0.28, 1),     # Vurgulu Kart
    "primary": (0.22, 0.58, 0.93, 1),       # Mühendislik Mavisi / Cyan
    "accent": (0.1, 0.75, 0.6, 1),          # Yeşil / Turkuaz Vurgu
    "text_main": (0.95, 0.96, 0.98, 1),     # Safa Yakın Beyaz
    "text_sub": (0.65, 0.70, 0.78, 1),      # İkincil Yazı
    "tbl_header": (0.20, 0.28, 0.38, 1),    # Tablo Başlık Background
    "tbl_unit": (0.16, 0.22, 0.30, 1),      # Tablo Birim Background
    "tbl_row_even": (0.14, 0.17, 0.22, 1),  # Tablo Çift Satır
    "tbl_row_odd": (0.11, 0.13, 0.17, 1),   # Tablo Tek Satır
    "border": (0.25, 0.30, 0.38, 1)         # İnce Kenarlık
}


class CardContainer(BoxLayout):
    """Yuvarlatılmış arka plana sahip, içeriğine göre boyutlanan kart."""

    def __init__(
        self,
        bg_color=THEME["bg_card"],
        radius=12,
        padding_dp=12,
        spacing_dp=10,
        **kwargs
    ):
        super().__init__(
            orientation="vertical",
            padding=dp(padding_dp),
            spacing=dp(spacing_dp),
            size_hint_y=None,
            **kwargs
        )

        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)],
            )

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class AutoLabel(Label):
    """Metni genişliğe göre kıran ve yüksekliğini otomatik ayarlayan Label."""

    def __init__(
        self,
        font_sp=FONT["body"],
        is_bold=False,
        text_color=THEME["text_main"],
        **kwargs
    ):
        super().__init__(
            font_size=sp(font_sp),
            bold=is_bold,
            color=text_color,
            size_hint=(1, None),
            valign="middle",
            halign="left",
            **kwargs
        )
        self.bind(width=self._update_text_size)
        self.bind(texture_size=self._update_height)

    def _update_text_size(self, instance, width):
        self.text_size = (max(0, width), None)

    def _update_height(self, instance, texture_size):
        self.height = max(texture_size[1] + dp(8), dp(28))


class SectionHeader(CardContainer):
    """Ana bölüm başlıkları için vurgulu kart."""

    def __init__(self, title_text, icon_str="■", **kwargs):
        super().__init__(
            bg_color=THEME["bg_header"],
            radius=8,
            padding_dp=10,
            spacing_dp=0,
            **kwargs
        )

        lbl = AutoLabel(
            text=f"{icon_str}  {title_text.upper()}",
            font_sp=FONT["section"],
            is_bold=True,
            text_color=THEME["primary"],
        )
        self.add_widget(lbl)


class ReportView(CardContainer):
    def __init__(self, report, **kwargs):
        super().__init__(bg_color=THEME["bg_card"], radius=10, padding_dp=12, **kwargs)

        if report is None:
            return

        # ------------------------------------------------
        # Başlık & Açıklama
        # ------------------------------------------------
        if getattr(report, "custom_title", None):
            self.add_widget(
                AutoLabel(
                    text=str(report.custom_title),
                    font_sp=FONT["heading"],
                    is_bold=True,
                    text_color=THEME["accent"]
                )
            )

        if getattr(report, "custom_desc", None):
            self.add_widget(
                AutoLabel(
                    text=str(report.custom_desc),
                    font_sp=FONT["small"],
                    text_color=THEME["text_sub"]
                )
            )

        # ------------------------------------------------
        # Tablo Tasarımı
        # ------------------------------------------------
        if hasattr(report, "columns") and len(report) > 0:
            columns = list(report.columns)
            has_desc = bool(getattr(report, "column_descriptions", None))
            has_units = bool(getattr(report, "column_units", None))

            extra_rows = 1 + (1 if has_desc else 0) + (1 if has_units else 0)
            row_count = extra_rows + len(report)
            
            # Kolon sayısına ve mobil ekran yapısına göre esnek genişlik
            col_width = dp(140)

            table = GridLayout(
                cols=len(columns),
                rows=row_count,
                size_hint=(None, None),
                spacing=dp(1),
                width=col_width * len(columns),
            )
            table.bind(minimum_height=table.setter("height"))

            # 1. Kolon Başlıkları
            for column in columns:
                table.add_widget(
                    self.cell(
                        str(column),
                        bold=True,
                        bg_color=THEME["tbl_header"],
                        font_sp=FONT["table"],
                        col_width=col_width
                    )
                )

            # 2. Açıklamalar
            if has_desc:
                for column in columns:
                    desc_text = report.column_descriptions.get(column, "")
                    table.add_widget(
                        self.cell(
                            desc_text,
                            bg_color=THEME["tbl_unit"],
                            text_color=THEME["text_sub"],
                            font_sp=FONT["small"],
                            col_width=col_width
                        )
                    )

            # 3. Birimler
            if has_units:
                for column in columns:
                    unit_text = report.column_units.get(column, "")
                    table.add_widget(
                        self.cell(
                            f"[{unit_text}]" if unit_text else "",
                            bg_color=THEME["tbl_unit"],
                            text_color=THEME["primary"],
                            font_sp=FONT["small"],
                            col_width=col_width
                        )
                    )

            # 4. Veri Satırları
            for idx, (_, row) in enumerate(report.iterrows()):
                values = report._format_row(row) if hasattr(report, "_format_row") else row.values
                row_bg = THEME["tbl_row_even"] if idx % 2 == 0 else THEME["tbl_row_odd"]
                for value in values:
                    table.add_widget(
                        self.cell(
                            str(value),
                            bg_color=row_bg,
                            font_sp=FONT["table"],
                            col_width=col_width
                        )
                    )

            # Tablo Yatay Kaydırma Kutusu (Dikey kaydırma kilitlenmesin diye do_scroll_y=False yapıldı)
            table_scroll = ScrollView(
                do_scroll_x=True,
                do_scroll_y=True,
                size_hint=(1, None),
            )
            # ScrollView yüksekliğini tablonun dinamik yüksekliğine güvenle bağlama
            def _update_scroll_height(instance, value):
                table_scroll.height = min(value + dp(12), dp(320))

            table.bind(height=_update_scroll_height)
            
            table_scroll.add_widget(table)
            self.add_widget(table_scroll)

        # ------------------------------------------------
        # Görseller
        # ------------------------------------------------
        graphics = getattr(report, "graphics", [])
        for g_item in graphics:
            g_title = g_item.get("title")
            g_desc = g_item.get("description")

            if g_title:
                self.add_widget(
                    AutoLabel(text=str(g_title), font_sp=FONT["heading"], is_bold=True, text_color=THEME["accent"])
                )
            if g_desc:
                self.add_widget(
                    AutoLabel(text=str(g_desc), font_sp=FONT["small"], text_color=THEME["text_sub"])
                )

            raw_graphic = g_item.get("image") if "image" in g_item else g_item.get("data")
            k_img = self._load_kivy_image(raw_graphic)
            if k_img:
                self.add_widget(k_img)

    def _load_kivy_image(self, raw_graphic):
        """Görselleri kart stiline uygun yükler."""
        if raw_graphic is None:
            return None

        try:
            buf = None
            if hasattr(raw_graphic, "savefig"):
                buf = io.BytesIO()
                raw_graphic.savefig(buf, format="png", bbox_inches="tight", facecolor="#15181e")
                buf.seek(0)
            elif isinstance(raw_graphic, io.BytesIO):
                buf = raw_graphic
                buf.seek(0)
            elif isinstance(raw_graphic, bytes):
                buf = io.BytesIO(raw_graphic)
                buf.seek(0)
            elif isinstance(raw_graphic, str):
                return Image(
                    source=raw_graphic,
                    size_hint_y=None,
                    height=dp(260),
                    allow_stretch=True,
                    keep_ratio=True
                )

            if buf:
                cim = CoreImage(buf, ext="png")
                return Image(
                    texture=cim.texture,
                    size_hint_y=None,
                    height=dp(260),
                    allow_stretch=True,
                    keep_ratio=True
                )
        except Exception as e:
            logging.error(f"Görsel dönüştürme hatası: {e}")
            return None
        return None

    @staticmethod
    def cell(text, bold=False, bg_color=THEME["tbl_row_even"], text_color=THEME["text_main"], font_sp=FONT["table"], col_width=dp(140)):
        """AutoLabel dinamizmini tablo hücrelerine uygulayan metod."""
        label = Label(
            text=str(text),
            size_hint=(None, None),
            width=col_width,
            halign="center",
            valign="middle",
            font_size=sp(font_sp),
            color=text_color,
            bold=bold
        )

        # İçeriğe göre dinamik genişlik kırma ve yükseklik hesabı
        def update_text_size(instance, width):
            instance.text_size = (max(0, width - dp(8)), None)

        def update_height(instance, texture_size):
            # Hücrenin iç metnine göre yüksekliği otomatik esnet (minimum 36dp)
            instance.height = max(texture_size[1] + dp(12), dp(36))

        label.bind(width=update_text_size)
        label.bind(texture_size=update_height)

        # Arka plan çizimi
        with label.canvas.before:
            Color(*bg_color)
            label._background = Rectangle(pos=label.pos, size=label.size)

        def update_bg(instance, value):
            instance._background.pos = instance.pos
            instance._background.size = instance.size

        label.bind(pos=update_bg, size=update_bg)
        return label


class StructuralAnalysisApp(App):

    def build(self):
        # Ana Arka Plan
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*THEME["bg_app"])
            root._bg = Rectangle(pos=root.pos, size=root.size)

        def _update_root_bg(instance, value):
            instance._bg.pos = instance.pos
            instance._bg.size = instance.size
        root.bind(pos=_update_root_bg, size=_update_root_bg)

        root_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        container = BoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(14),
            size_hint_y=None,
        )
        container.bind(minimum_height=container.setter("height"))

        # ------------------------------------------------
        # 1. KAR YÜKÜ HESAPLARI
        # ------------------------------------------------
        container.add_widget(SectionHeader("Kar Yükü Hesapları"))
        
        snow_config = proje_data["snow_config"]
        snow = SnowLoad(snow_config)
        snow_rep = snow.report()

        if hasattr(snow_rep, "columns"):
            container.add_widget(ReportView(snow_rep))
        else:
            card = CardContainer()
            card.add_widget(AutoLabel(text=str(snow_rep)))
            container.add_widget(card)

        # ------------------------------------------------
        # 2. DEPREM YÜKÜ HESAPLARI
        # ------------------------------------------------
        container.add_widget(SectionHeader("Deprem Yükü Hesapları"))
        
        eq_data = proje_data["earthquake_config"]
        eq = Spectrum(eq_data)
        eq.run()

        if hasattr(eq, "table_parameters"):
            container.add_widget(ReportView(eq.table_parameters))

        if hasattr(eq, "table_spectrum"):
            container.add_widget(ReportView(eq.table_spectrum))

        # ------------------------------------------------
        # 3. RÜZGAR YÜKÜ HESAPLARI
        # ------------------------------------------------
        container.add_widget(SectionHeader("Rüzgar Yükü Hesapları"))
        
        wind_report = WindReport(proje_data)
        wind_report.analyze()
        w_report = wind_report.report()

        params = w_report.get("parameters", {})
        param_card = CardContainer(bg_color=THEME["bg_card"])
        param_card.add_widget(
            AutoLabel(text="Genel Rüzgar Parametreleri", font_sp=FONT["heading"], is_bold=True, text_color=THEME["accent"])
        )
        
        param_text = "\n".join([f"• {k}: {v}" for k, v in params.items()])
        param_card.add_widget(AutoLabel(text=param_text, font_sp=FONT["body"], text_color=THEME["text_sub"]))
        container.add_widget(param_card)

        for w_key in wind_report.results:
            dir_data = w_report.get(w_key, {})

            dir_card = CardContainer(bg_color=THEME["bg_card"])
            dir_card.add_widget(
                AutoLabel(
                    text=f"Rüzgar Yönü / Aksı: {w_key}",
                    font_sp=FONT["heading"],
                    is_bold=True,
                    text_color=THEME["primary"]
                )
            )

            # Görsel Yükleme
            image_data = dir_data.get("image")
            if image_data:
                temp_rv = ReportView(None)
                k_img = temp_rv._load_kivy_image(image_data)
                if k_img:
                    dir_card.add_widget(k_img)

            cpe_rep = dir_data.get("cpe")
            if cpe_rep is not None and hasattr(cpe_rep, "columns"):
                dir_card.add_widget(ReportView(cpe_rep))

            wf_rep = dir_data.get("wind_force")
            if wf_rep is not None and hasattr(wf_rep, "columns"):
                dir_card.add_widget(ReportView(wf_rep))

            container.add_widget(dir_card)

        root_scroll.add_widget(container)
        root.add_widget(root_scroll)
        return root


if __name__ == "__main__":
    StructuralAnalysisApp().run()