import sys
import traceback
from io import BytesIO

# ============================================================
# Android log
# ============================================================

LOG_PATH = "/sdcard/KivyProjeleri/test3.log"

log_file = None

try:
    log_file = open(
        LOG_PATH,
        "w",
        encoding="utf-8",
    )

    sys.stdout = log_file
    sys.stderr = log_file

except Exception:
    log_file = None


def log(message):
    print(message, flush=True)


# ============================================================
# Imports
# ============================================================

try:
    import pandas as pd

    from kivy.app import App
    from kivy.core.image import Image as CoreImage
    from kivy.graphics import Color, Rectangle
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.image import Image
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout

    from PIL import Image as PILImage
    from PIL import ImageDraw

    from utils.report_dataframe import ReportDataFrame

    log("Imports OK")

    # ========================================================
    # Test grafik
    # ========================================================

    def create_test_graphic():

        image = PILImage.new(
            "RGB",
            (900, 450),
            "white",
        )

        draw = ImageDraw.Draw(image)

        # Basit eksen
        draw.line(
            (80, 370, 820, 370),
            fill="black",
            width=3,
        )

        draw.line(
            (80, 370, 80, 60),
            fill="black",
            width=3,
        )

        # Test eğrisi
        points = [
            (100, 330),
            (200, 280),
            (300, 300),
            (400, 190),
            (500, 230),
            (600, 130),
            (700, 170),
            (800, 90),
        ]

        draw.line(
            points,
            fill="red",
            width=5,
        )

        # Noktalar
        for x, y in points:
            draw.ellipse(
                (x - 7, y - 7, x + 7, y + 7),
                fill="blue",
            )

        buffer = BytesIO()

        image.save(
            buffer,
            format="PNG",
        )

        buffer.seek(0)

        return buffer

    # ========================================================
    # ReportDataFrame → Kivy
    # ========================================================

    class ReportView(BoxLayout):

        def __init__(
            self,
            report,
            **kwargs,
        ):

            super().__init__(
                orientation="vertical",
                spacing=10,
                padding=10,
                **kwargs,
            )

            # ------------------------------------------------
            # Başlık
            # ------------------------------------------------

            if report.custom_title:

                title = Label(
                    text=str(
                        report.custom_title
                    ),
                    size_hint_y=None,
                    height=45,
                    font_size=22,
                    bold=True,
                )

                self.add_widget(title)

            # ------------------------------------------------
            # Açıklama
            # ------------------------------------------------

            if report.custom_desc:

                desc = Label(
                    text=str(
                        report.custom_desc
                    ),
                    size_hint_y=None,
                    height=60,
                    text_size=(None, None),
                    halign="left",
                    valign="middle",
                )

                self.add_widget(desc)

            # ------------------------------------------------
            # Tablo
            # ------------------------------------------------

            table_scroll = ScrollView(
                do_scroll_x=True,
                do_scroll_y=True,
            )

            columns = list(report.columns)

            # Header + description + units + data
            extra_rows = 1

            if report.column_descriptions:
                extra_rows += 1

            if report.column_units:
                extra_rows += 1

            row_count = extra_rows + len(report)

            table = GridLayout(
                cols=len(columns),
                rows=row_count,
                size_hint=(None, None),
                spacing=1,
            )

            cell_width = 150
            cell_height = 42

            table.width = (
                cell_width * len(columns)
            )

            table.height = (
                cell_height * row_count
            )

            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            for column in columns:

                table.add_widget(
                    self.cell(
                        str(column),
                        bold=True,
                    )
                )

            # ------------------------------------------------
            # Column descriptions
            # ------------------------------------------------

            if report.column_descriptions:

                for column in columns:

                    table.add_widget(
                        self.cell(
                            report.column_descriptions.get(
                                column,
                                "",
                            )
                        )
                    )

            # ------------------------------------------------
            # Units
            # ------------------------------------------------

            if report.column_units:

                for column in columns:

                    table.add_widget(
                        self.cell(
                            report.column_units.get(
                                column,
                                "",
                            )
                        )
                    )

            # ------------------------------------------------
            # Data
            # ------------------------------------------------

            for _, row in report.iterrows():

                values = report._format_row(row)

                for value in values:

                    table.add_widget(
                        self.cell(
                            value
                        )
                    )

            table_scroll.add_widget(table)

            self.add_widget(
                table_scroll
            )

            # ------------------------------------------------
            # Graphics
            # ------------------------------------------------

            for graphic in report.graphics:

                graphic_title = (
                    graphic.get("title")
                )

                graphic_desc = (
                    graphic.get("description")
                )

                if graphic_title:

                    self.add_widget(
                        Label(
                            text=str(
                                graphic_title
                            ),
                            size_hint_y=None,
                            height=40,
                            font_size=18,
                            bold=True,
                        )
                    )

                if graphic_desc:

                    self.add_widget(
                        Label(
                            text=str(
                                graphic_desc
                            ),
                            size_hint_y=None,
                            height=45,
                        )
                    )

                data = graphic["data"]

                data.seek(0)

                kivy_image = Image(
                    texture=CoreImage(
                        data,
                        ext="png",
                    ).texture,
                    size_hint_y=None,
                    height=300,
                    allow_stretch=True,
                    keep_ratio=True,
                )

                self.add_widget(
                    kivy_image
                )

        # ----------------------------------------------------
        # Hücre
        # ----------------------------------------------------

        @staticmethod
        def cell(
            text,
            bold=False,
        ):

            label = Label(
                text=str(text),
                size_hint=(
                    None,
                    None,
                ),
                width=150,
                height=42,
                text_size=(
                    140,
                    38,
                ),
                halign="center",
                valign="middle",
            )

            if bold:
                label.bold = True

            with label.canvas.before:
                Color(
                    0.92,
                    0.92,
                    0.92,
                    1,
                )

                label._background = Rectangle(
                    pos=label.pos,
                    size=label.size,
                )

            def update_background(
                instance,
                value,
            ):
                instance._background.pos = (
                    instance.pos
                )
                instance._background.size = (
                    instance.size
                )

            label.bind(
                pos=update_background,
                size=update_background,
            )

            return label

    # ========================================================
    # Test verisi
    # ========================================================

    def create_report():

        data = {
            "Bölge": [
                "A",
                "B",
                "C",
                "D",
                "E",
            ],
            "Yüzey": [
                "Duvar",
                "Duvar",
                "Duvar",
                "Çatı",
                "Çatı",
            ],
            "Tablo": [
                "7.1",
                "7.1",
                "7.1",
                "7.3",
                "7.3",
            ],
            "Yön": [
                0,
                45,
                90,
                180,
                270,
            ],
            "Eğim": [
                0.0,
                0.0,
                0.0,
                18.30,
                18.30,
            ],
            "Cpe,10 min": [
                -1.20,
                -0.80,
                -0.70,
                -0.90,
                -1.10,
            ],
            "Cpe,10 max": [
                0.80,
                0.70,
                0.80,
                0.20,
                0.30,
            ],
        }

        report = ReportDataFrame(
            data,

            custom_title=(
                "Dış Basınç Katsayıları"
            ),

            custom_desc=(
                "Rüzgar bölgelerine ait "
                "dış basınç katsayıları."
            ),

            column_descriptions={
                "Bölge": "Rüzgar bölgesi",
                "Yüzey": "Yapı yüzeyi",
                "Tablo": "Standart tablo",
                "Yön": "Rüzgar yönü",
                "Eğim": "Çatı eğimi",
                "Cpe,10 min": "Minimum dış basınç",
                "Cpe,10 max": "Maksimum dış basınç",
            },

            column_units={
                "Yön": "°",
                "Eğim": "°",
                "Cpe,10 min": "",
                "Cpe,10 max": "",
            },

            column_formats={
                "Yön": ".0f",
                "Eğim": ".2f",
                "Cpe,10 min": ".3f",
                "Cpe,10 max": ".3f",
            },
        )

        # ----------------------------------------------------
        # Grafik
        # ----------------------------------------------------

        graphic = create_test_graphic()

        report.add_graphic(
            graphic,
            title="Rüzgar Bölgesi Grafiği",
            description=(
                "Tablo ile ilişkili örnek grafik."
            ),
        )

        return report

    # ========================================================
    # Kivy App
    # ========================================================

    class TestApp(App):

        def build(self):

            log("TestApp.build()")

            report = create_report()

            log(
                f"DataFrame: "
                f"{report.shape}"
            )

            log(
                f"Graphics: "
                f"{len(report.graphics)}"
            )

            root = BoxLayout(
                orientation="vertical"
            )

            view = ReportView(
                report
            )

            root.add_widget(view)

            log("ReportView oluşturuldu")

            return root

    # ========================================================
    # Run
    # ========================================================

    log("Kivy başlatılıyor...")

    TestApp().run()

except Exception:

    if log_file:
        traceback.print_exc(
            file=log_file
        )
        log_file.flush()
    else:
        traceback.print_exc()

finally:

    if log_file:
        log_file.flush()
        log_file.close()