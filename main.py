import io
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage

from data.defaults import proje_data
from loads.snow_load import SnowLoad
from loads.spectrum import Spectrum

from windcalc.wind_results import WindReport
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

class AutoLabel(Label):
    """Metin uzunluğuna göre yüksekliğini otomatik ayarlayan ve metni kıran Label."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        # Yatayda kırılmayı aktifleştir
        self.bind(width=self._update_text_size)
        # Metin dokusu oluştukça yüksekliği güncelle
        self.bind(texture_size=self._update_height)

    def _update_text_size(self, instance, value):
        self.text_size = (value - 20, None)

    def _update_height(self, instance, value):
        # En az 30px yükseklik sağla
        self.height = max(value[1] + 15, 30)


class ReportView(BoxLayout):
    def __init__(self, report, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=10,
            padding=10,
            size_hint_y=None,
            **kwargs
        )
        self.bind(minimum_height=self.setter("height"))

        if report is None:
            return

        # ------------------------------------------------
        # Başlık & Açıklama
        # ------------------------------------------------
        if getattr(report, "custom_title", None):
            self.add_widget(AutoLabel(text=str(report.custom_title), font_size=20, bold=True))

        if getattr(report, "custom_desc", None):
            self.add_widget(AutoLabel(text=str(report.custom_desc), font_size=14))

        # ------------------------------------------------
        # Tablo
        # ------------------------------------------------
        if hasattr(report, "columns") and len(report) > 0:
            columns = list(report.columns)
            extra_rows = 1
            if getattr(report, "column_descriptions", None): extra_rows += 1
            if getattr(report, "column_units", None): extra_rows += 1

            row_count = extra_rows + len(report)
            cell_width, cell_height = 160, 45

            table = GridLayout(
                cols=len(columns),
                rows=row_count,
                size_hint=(None, None),
                spacing=1,
                width=cell_width * len(columns),
                height=cell_height * row_count
            )

            for column in columns:
                table.add_widget(self.cell(str(column), bold=True))

            if getattr(report, "column_descriptions", None):
                for column in columns:
                    table.add_widget(self.cell(report.column_descriptions.get(column, "")))

            if getattr(report, "column_units", None):
                for column in columns:
                    table.add_widget(self.cell(report.column_units.get(column, "")))

            for _, row in report.iterrows():
                values = report._format_row(row) if hasattr(report, "_format_row") else row.values
                for value in values:
                    table.add_widget(self.cell(str(value)))

            table_scroll = ScrollView(
                do_scroll_x=True, do_scroll_y=False,
                size_hint_y=None, height=cell_height * min(row_count, 8) + 15
            )
            table_scroll.add_widget(table)
            self.add_widget(table_scroll)

        # ------------------------------------------------
        # Görseller (DÜZELTİLEN KISIM HERE)
        # ------------------------------------------------
        graphics = getattr(report, "graphics", [])
        for g_item in graphics:
            g_title = g_item.get("title")
            g_desc = g_item.get("description")

            if g_title:
                self.add_widget(AutoLabel(text=str(g_title), font_size=16, bold=True))
            if g_desc:
                self.add_widget(AutoLabel(text=str(g_desc), font_size=13))

            # Anahtar hem "image" hem de "data" için kontrol ediliyor
            raw_graphic = g_item.get("image") if "image" in g_item else g_item.get("data")
            
            k_img = self._load_kivy_image(raw_graphic)
            if k_img:
                self.add_widget(k_img)

    def _load_kivy_image(self, raw_graphic):
        """BytesIO, Matplotlib Figure veya Dosya Yolundan Kivy Image üretir."""
        if raw_graphic is None:
            return None

        try:
            buf = None

            # 1. Eğer Matplotlib Figure nesnesi geldiyse BytesIO'ya kaydet
            if hasattr(raw_graphic, "savefig"):
                buf = io.BytesIO()
                raw_graphic.savefig(buf, format="png", bbox_inches="tight")
                buf.seek(0)

            # 2. Eğer halihazırda BytesIO ise başa sar
            elif isinstance(raw_graphic, io.BytesIO):
                buf = raw_graphic
                buf.seek(0)

            # 3. Eğer ham bytes ise BytesIO'ya sar
            elif isinstance(raw_graphic, bytes):
                buf = io.BytesIO(raw_graphic)
                buf.seek(0)

            # 4. Dosya yolu (str) ise doğrudan Image ile döndür
            elif isinstance(raw_graphic, str):
                return Image(
                    source=raw_graphic,
                    size_hint_y=None,
                    height=320,
                    allow_stretch=True,
                    keep_ratio=True
                )

            if buf:
                # CoreImage tamponu okur
                cim = CoreImage(buf, ext="png")
                return Image(
                    texture=cim.texture,
                    size_hint_y=None,
                    height=320,
                    allow_stretch=True,
                    keep_ratio=True
                )

        except Exception as e:
            print(f"[HATA] Görsel Kivy texture'a dönüştürülemedi: {e}")
            return None

        return None

    @staticmethod
    def cell(text, bold=False):
        label = Label(
            text=str(text),
            size_hint=(None, None),
            width=160,
            height=45,
            text_size=(150, 40),
            halign="center",
            valign="middle",
            color=(0, 0, 0, 1)
        )
        if bold:
            label.bold = True

        with label.canvas.before:
            Color(0.8, 0.85, 0.9, 1) if bold else Color(0.93, 0.93, 0.93, 1)
            label._background = Rectangle(pos=label.pos, size=label.size)

        def update_bg(instance, value):
            instance._background.pos = instance.pos
            instance._background.size = instance.size

        label.bind(pos=update_bg, size=update_bg)
        return label


class StructuralAnalysisApp(App):

    def build(self):
        root_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        container = BoxLayout(
            orientation="vertical",
            spacing=25,
            padding=20,
            size_hint_y=None,
        )
        container.bind(minimum_height=container.setter("height"))

        # ------------------------------------------------
        # 1. Kar Yükü
        # ------------------------------------------------
        container.add_widget(
            AutoLabel(
                text="KAR YÜKÜ HESAPLARI",
                font_size=22,
                bold=True,
                color=(0, 0.2, 0.5, 1),
            )
        )
        snow_config = proje_data["snow_config"]
        snow = SnowLoad(snow_config)
        snow_rep = snow.report()

        if hasattr(snow_rep, "columns"):
            container.add_widget(ReportView(snow_rep))
        else:
            container.add_widget(AutoLabel(text=str(snow_rep)))

        # ------------------------------------------------
        # 2. Deprem Spektrumu
        # ------------------------------------------------
        container.add_widget(
            AutoLabel(
                text="DEPREM YÜKÜ HESAPLARI",
                font_size=22,
                bold=True,
                color=(0, 0.2, 0.5, 1),
            )
        )
        eq_data = proje_data["earthquake_config"]
        eq = Spectrum(eq_data)
        eq.run()

        if hasattr(eq, "table_parameters"):
            container.add_widget(ReportView(eq.table_parameters))

        if hasattr(eq, "table_spectrum"):
            container.add_widget(ReportView(eq.table_spectrum))
        
        # ------------------------------------------------
        # 3. Rüzgar Yükü
        # ------------------------------------------------
        container.add_widget(
            AutoLabel(
                text="RÜZGAR YÜKÜ HESAPLARI",
                font_size=22,
                bold=True,
                color=(0, 0.2, 0.5, 1),
            )
        )
        wind_report = WindReport(proje_data)
        wind_report.analyze()
        w_report = wind_report.report()

        params = w_report.get("parameters", {})
        param_text = "Rüzgar Parametreleri:\n" + "\n".join(
            [f"• {k}: {v}" for k, v in params.items()]
        )
        container.add_widget(
            AutoLabel(text=param_text, font_size=14, color=(0.2, 0.2, 0.2, 1))
        )

        for w_key in wind_report.results:
            dir_data = w_report.get(w_key, {})

            container.add_widget(
                AutoLabel(
                    text=f"Rüzgar Yönü: {w_key}",
                    font_size=18,
                    bold=True,
                    color=(0.1, 0.3, 0.1, 1),
                )
            )

            # Görsel Yükleme
            image_data = dir_data.get("image")
            if image_data:
                # Helper metod üzerinden güvenli yükleme
                temp_rv = ReportView(None)
                k_img = temp_rv._load_kivy_image(image_data)
                if k_img:
                    container.add_widget(k_img)

            cpe_rep = dir_data.get("cpe")
            if cpe_rep is not None and hasattr(cpe_rep, "columns"):
                container.add_widget(ReportView(cpe_rep))

            wf_rep = dir_data.get("wind_force")
            if wf_rep is not None and hasattr(wf_rep, "columns"):
                container.add_widget(ReportView(wf_rep))

        root_scroll.add_widget(container)
        return root_scroll


if __name__ == "__main__":
    StructuralAnalysisApp().run()