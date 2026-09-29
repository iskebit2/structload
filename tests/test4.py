from data.defaults import proje_data
from loads.snow_load import SnowLoad
from loads.spectrum import EarthquakeLoad
from loads.spectrum_kivy import SpectrumPlot
from windcalc.wind_analyzer import WindAnalyzer
from windcalc.wind_results import WindReport


config= proje_data['snow_config']
snow = SnowLoad(config)
print(snow.report())
data = proje_data['earthquake_config']
eq = EarthquakeLoad(**data)
sp = SpectrumPlot()
sp.set_spectrum(eq)
report = eq.report()
print(report)
wind_report = WindReport(proje_data)
wind_report.analyze()

w_report = wind_report.report()

parameters_ = w_report['parameters']
print(parameters_)
for w_key in wind_report.results:
    print(f"Wind Dir: {w_key}")
    image_ = w_report[w_key].get('image', None)
    cpe_ = w_report[w_key].get('cpe', None)
    wind_force_ = w_report[w_key].get('wind_force', None)
    print(image_)
    print(cpe_)
    print(wind_force_)