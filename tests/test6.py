from data.defaults import proje_data
from loads.spectrum import Spectrum
from utils.my_document import MyDocument

data = proje_data['earthquake_config']
eq = Spectrum(data)
eq.run()

doc = MyDocument()
doc.apply_visual_settings()

doc.add_heading_numbered("STATİK RAPOR", level=1)
eq.table_parameters.save_to_docx(doc)
eq.table_spectrum.save_to_docx(doc)
out = "spectrum.docx"
if doc.save_report(out):
    print(f"\n✅ Kaydedildi: {out}")
else:
    print("\n❌ Kaydedilemedi")