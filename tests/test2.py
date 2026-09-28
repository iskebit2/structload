# test2.py
"""
Statik rapor oluşturma — tüm yük motorlarını (kar, deprem, rüzgar)
ve proje_data'yı ReportDataFrame listesine çevirir.
"""

from pathlib import Path

from data.defaults import proje_data
from data.mechanical import woodMaterial
from data.material_data import MATERIAL_LIBRARY

from loads.snow_load import SnowLoad
from loads.spectrum import EarthquakeLoad
from loads.spectrum_kivy import SpectrumPlot
from windcalc.wind_results import WindReport

from utils.report_dataframe import ReportDataFrame
from utils.my_document import myDocument


# ============================================================
# YARDIMCI: dict → ReportDataFrame
# ============================================================

def _guze_etiket(k: str) -> str:
    return k.replace("_", " ").strip().capitalize()


def _kisa_goster(v) -> str:
    if isinstance(v, dict):
        return f"({len(v)} alan)"
    if isinstance(v, list):
        return f"({len(v)} öğe)"
    return str(v)


def dict_to_df(d: dict, title: str, desc: str = "") -> ReportDataFrame:
    """Basit dict → 'Parametre | Değer' tablosu."""
    rows = []
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            v = _kisa_goster(v)
        rows.append({"Parametre": _guze_etiket(k), "Değer": v})
    return ReportDataFrame(rows, custom_title=title, custom_desc=desc)


# ============================================================
# RAPOR TABLOLARI — proje_data + tüm yük motorları
# ============================================================

def create_report_tables(pdata: dict) -> list:
    """
    proje_data'dan tam rapor tablo listesi üretir:
    proje bilgileri + yönetmelikler + malzemeler + yükler
    + kar + deprem + rüzgar + yük birleşimleri
    """
    tables = []

    # ---------- 1. Proje Bilgileri ----------
    tables.append(dict_to_df(
        pdata["proje_bilgileri"],
        title="1. Proje Bilgileri",
        desc="Projenin kimlik ve künye bilgileri.",
    ))

    # ---------- 2. Yönetmelikler ----------
    regulations = {
        "Yönetmelik ve Standart": [
            "AHŞAP BİNALARIN TASARIM, HESAP VE YAPIM ESASLARINA DAİR YÖNETMELİK (2025)",
            "Tasarım Örnekleri Kılavuzu",
            "TS EN 1995-1-1: Eurocode 5",
            "TS EN 1990",
            "TS EN 1991",
            "TBDY 2018",
            "TS EN 338",
            "TS 498",
        ],
        "Açıklama": [
            "Bu projenin tasarım ve hesap esaslarını belirleyen ana yönetmeliktir.",
            "Yönetmeliğin ekinde yer alan ve tasarımcılara yol gösteren kılavuz",
            "Yapı Tasarımı İçin Esaslar, Ahşap Yapılar ve Elemanlarının Tasarımı",
            "Eurocode - Yapıların Tasarımı için Esaslar",
            "Eurocode 1 - Yapı Üzerindeki Etkiler (Kar, Rüzgar, Hareketli Yükler)",
            "Türkiye Bina Deprem Yönetmeliği",
            "Yapısal Ahşap - Dayanım Sınıfları",
            "Yapı Elemanlarının Boyutlandırılmasında Alınacak Yüklerin Hesap Değerleri",
        ],
    }
    tables.append(ReportDataFrame(
        regulations,
        custom_title="2. Yönetmelik ve Standartlar",
        custom_desc="Hesaplarda kullanılan ulusal ve uluslararası yönetmelikler.",
    ))

    # ---------- 3. Saha ve Deprem (TBDY 2018) ----------
    tables.append(dict_to_df(
        pdata["saha_ve_deprem"],
        title="3. Saha ve Deprem Parametreleri",
        desc="TBDY 2018'e göre zemin, spektrum ve deprem parametreleri.",
    ))

    # ---------- 4. Malzeme Sınıfları (kaba) ----------
    malz_rows = [
        {"Eleman Grubu": _guze_etiket(k), "Malzeme Sınıfı": v}
        for k, v in pdata["malzemeler"].items()
    ]
    tables.append(ReportDataFrame(
        malz_rows,
        custom_title="4. Malzeme Sınıfları",
        custom_desc="Yapıda kullanılan malzeme sınıfları ve standartları.",
    ))

    # ---------- 5. Ahşap Malzeme Mekanik Özellikleri ----------
    wood = woodMaterial(pdata["malzemeler"].get("ahsap", "C24"))
    wood_rows = [
        {"Parametre": k, "Değer": v, "Birim": wood.units.get(k, "-")}
        for k, v in wood.param.items()
    ]
    tables.append(ReportDataFrame(
        wood_rows,
        custom_title=f"5. Ahşap Malzeme Özellikleri — {wood.material}",
        custom_desc="TS EN 338'e göre yapısal dayanım parametreleri.",
    ))

    # ---------- 6. Ölü Yükler (G) ----------
    for grup_adi, grup in pdata["yukler"]["olu_yukler_G"].items():
        rows = []
        for i, det in enumerate(grup["details"], 1):
            mat = det.get("malzeme_ref") or {}
            rows.append({
                "#": i,
                "Bileşen": det["ad"],
                "Malzeme": mat.get("name", "-"),
                "Ağırlık (kN/m³)": mat.get("weight", "-"),
                "Kalınlık (m)": det.get("thickness_m", "-"),
                "Değer (kN/m²)": det.get("hesaplanan_yuk_kN_m2", 0),
            })
        rows.append({
            "#": "", "Bileşen": "TOPLAM", "Malzeme": "",
            "Ağırlık (kN/m³)": "", "Kalınlık (m)": "",
            "Değer (kN/m²)": grup.get("toplam_yuk", 0),
        })
        tables.append(ReportDataFrame(
            rows,
            custom_title=f"6. Ölü Yük — {_guze_etiket(grup_adi)}",
            custom_desc=f"Birim: {grup.get('birim', 'kN/m²')}",
            column_units={"Değer (kN/m²)": "kN/m²", "Ağırlık (kN/m³)": "kN/m³"},
        ))

    # ---------- 7. Hareketli Yükler (Q) ----------
    for grup_adi, grup in pdata["yukler"]["hareketli_yukler_Q"].items():
        rows = [
            {"Parametre": "Yük Değeri (qk)", "Değer": grup.get("qk", 0),
             "Birim": grup.get("birim", "kN/m²")},
            {"Parametre": "ψ₂ Katılım Katsayısı",
             "Değer": grup.get("psi_2_katilim_katsayisi", "-"), "Birim": "-"},
            {"Parametre": "Açıklama",
             "Değer": grup.get("description", "-"), "Birim": "-"},
        ]
        tables.append(ReportDataFrame(
            rows,
            custom_title=f"7. Hareketli Yük — {_guze_etiket(grup_adi)}",
            custom_desc="TS EN 1991-1-1'e göre hareketli yük.",
        ))

    # ---------- 8. KAR YÜKÜ (SnowLoad.report) ----------
    try:
        snow = SnowLoad(pdata["snow_config"])
        tables.append(snow.report())
    except Exception as e:
        print(f"⚠️  Kar yükü raporu üretilemedi: {e}")

    # ---------- 9. RÜZGAR YÜKÜ (WindReport.report) ----------
    try:
        

        wind = WindReport(pdata)
        wind.analyze()
        wind_result = wind.report()

        if isinstance(wind_result, dict) and "parameters" in wind_result:
            # ---- Parametreler (1 kez) ----
            df_param = wind_result["parameters"]
            if not isinstance(df_param, ReportDataFrame):
                # Düz DataFrame ise ReportDataFrame'e çevir
                df_param = ReportDataFrame(
                    df_param.reset_index(drop=True).to_dict("records"),
                    custom_title="8. Rüzgar Yükü — Parametreler",
                    custom_desc="TS EN 1991-1-4'e göre temel rüzgar parametreleri.",
                )
            else:
                df_param.custom_title = "8. Rüzgar Yükü — Parametreler"
                df_param.custom_desc = (
                    "TS EN 1991-1-4'e göre temel rüzgar parametreleri. "
                    "Bu değerler tüm yönler için ortaktır."
                )
            tables.append(df_param)

            # ---- Yön bazlı tablolar (4 yön × 2 tablo) ----
            yon_sirasi = ["x+", "x-", "y+", "y-"]
            for yon in yon_sirasi:
                if yon not in wind_result:
                    continue

                blok = wind_result[yon]
                if not isinstance(blok, dict):
                    continue

                # cpe tablosu
                if "cpe" in blok:
                    df_cpe = blok["cpe"]
                    if not isinstance(df_cpe, ReportDataFrame):
                        df_cpe = ReportDataFrame(
                            df_cpe.reset_index(drop=True).to_dict("records"),
                            custom_title=f"8.{yon_sirasi.index(yon)+1} Rüzgar — Yön {yon} — Basınç Katsayıları (Cpe)",
                            custom_desc=f"Yön: {yon}  |  Yüzey ve bölge bazlı dış basınç katsayıları.",
                        )
                    else:
                        df_cpe.custom_title = (
                            f"8.{yon_sirasi.index(yon)+1} Rüzgar — Yön {yon} "
                            f"— Basınç Katsayıları (Cpe)"
                        )
                        df_cpe.custom_desc = (
                            f"Yön: {yon}  |  Yüzey ve bölge bazlı dış basınç katsayıları."
                        )
                    tables.append(df_cpe)

                # wind_force tablosu
                if "wind_force" in blok:
                    df_wf = blok["wind_force"]
                    if not isinstance(df_wf, ReportDataFrame):
                        df_wf = ReportDataFrame(
                            df_wf.reset_index(drop=True).to_dict("records"),
                            custom_title=f"8.{yon_sirasi.index(yon)+1}.b Rüzgar — Yön {yon} — Kuvvet Değerleri",
                            custom_desc=f"Yön: {yon}  |  Net rüzgar kuvvetleri (kN/m²).",
                        )
                    else:
                        df_wf.custom_title = (
                            f"8.{yon_sirasi.index(yon)+1}.b Rüzgar — Yön {yon} "
                            f"— Kuvvet Değerleri"
                        )
                        df_wf.custom_desc = f"Yön: {yon}  |  Net rüzgar kuvvetleri (kN/m²)."
                    tables.append(df_wf)

        elif isinstance(wind_result, ReportDataFrame):
            # Tek tablo döndürüyorsa direkt ekle
            wind_result.custom_title = "8. Rüzgar Yükü"
            tables.append(wind_result)

        else:
            # Bilinmeyen format → string'e çevir, uyarı ver
            print(f"⚠️  Rüzgar raporu beklenmeyen tipte: {type(wind_result)}")
            tables.append(ReportDataFrame(
                [{"Uyarı": f"Rüzgar raporu okunamadı: {type(wind_result)}"}],
                custom_title="8. Rüzgar Yükü (okunamadı)",
            ))

    except Exception as e:
        print(f"⚠️  Rüzgar yükü raporu üretilemedi: {e}")
        import traceback
        traceback.print_exc()

    # ---------- 10. DEPREM YÜKÜ (EarthquakeLoad.report) ----------
    try:
        eq = EarthquakeLoad(**pdata["earthquake_config"])
        tables.append(eq.report())
    except Exception as e:
        print(f"⚠️  Deprem raporu üretilemedi: {e}")

    # ---------- 11. Yük Birleşimleri (load_cases) ----------
    if "load_cases" in pdata:
        lc = pdata["load_cases"]
        rows = []
        for k, v in lc.items():
            if isinstance(v, list):
                rows.append({
                    "Kategori": _guze_etiket(k),
                    "Adet": len(v),
                    "Liste": ", ".join(map(str, v)) if v else "-",
                })
        tables.append(ReportDataFrame(
            rows,
            custom_title="11. Yük Birleşimleri (Load Cases)",
            custom_desc="SAP2000'e aktarılacak yük birleşim isimleri.",
        ))

    return tables


# ============================================================
# WORD RAPORU
# ============================================================

def main():
    print("=" * 60)
    print("🏗️  STATİK RAPOR OLUŞTURMA")
    print("=" * 60)

    tables = create_report_tables(proje_data)
    print(f"\n📋 {len(tables)} tablo üretildi.")

    doc = myDocument()
    doc.apply_visual_settings()

    doc.add_heading_numbered("STATİK RAPOR", level=1)
    doc.add_paragraph(
        f"Proje: {proje_data['proje_bilgileri']['proje_adi']}  |  "
        f"Rev: {proje_data['proje_bilgileri']['revizyon']}"
    )
    doc.doc.add_paragraph()

    for i, table in enumerate(tables, 1):
        try:
            if hasattr(table, "round_floats"):
                table = table.round_floats(3)
            table.save_to_docx(doc, level=2)

            # Spektrum görseli (deprem tablosundan sonra)
            title = str(getattr(table, "custom_title", "") or "")
            if "Spektrum" in title or "Deprem" in title:
                img = Path("deprem_spektrumlari.png")
                if img.exists():
                    doc.add_paragraph("Şekil: Deprem Tepki Spektrumu")
                    doc.add_image(str(img), width_cm=15)
        except Exception as e:
            print(f"⚠️  Tablo {i} eklenemedi: {e}")

    out = "statik_rapor.docx"
    if doc.save_report(out):
        print(f"\n✅ Kaydedildi: {out}")
    else:
        print("\n❌ Kaydedilemedi")


if __name__ == "__main__":
    main()