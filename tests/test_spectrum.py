# tests/test_spectrum.py

from loads.spectrum import EarthquakeLoad


def test_spectrum_creation():

    eq = EarthquakeLoad(
        R=2.5,
        D=2.5,
        I=1.2,
        kappa=0.5,
        Hn=10.1,
        gamma_E=0.9,
        n=0.30,
        e="±0.05",
        zemin_sinifi="ZC",
    )

    assert eq is not None

def test_spectrum_calculation():

    eq = EarthquakeLoad(
        R=2.5,
        D=2.5,
        I=1.2,
        kappa=0.5,
        Hn=10.1,
        gamma_E=0.9,
        n=0.30,
        e="±0.05",
        zemin_sinifi="ZC",
    )

    eq.calculate()

    assert eq.Sae_DD2 is not None
    assert eq.Sae_DD3 is not None

    assert len(eq.T_values) == len(eq.Sae_DD2)
    assert len(eq.T_values) == len(eq.Sae_DD3)