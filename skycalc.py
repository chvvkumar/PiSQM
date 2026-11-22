# Sky brightness maths, kept free of hardware imports so it can be checked anywhere.
# Run "python skycalc.py" for the self-check.

import math

DARK_LIMIT = 25.0  # Reported when no signal is left above the dark offset


def mpsas_from_samples(samples, m0, ga, dark=0.0):
    """
    Average flux samples (uW/cm2, full minus IR) and convert to mag/arcsec^2.

    Averaging happens in linear flux, not in magnitudes, so noisy readings near
    the sensor floor (including zero and negative ones) cancel out instead of
    biasing the result. 'dark' is the flux the sensor reports with the dome
    capped; it is removed before the conversion.

    Returns (mpsas, mean_flux). mean_flux is before dark subtraction, which is
    the number to read off when measuring the dark offset.
    """
    if not samples:
        return DARK_LIMIT, 0.0
    mean_flux = sum(samples) / len(samples)
    signal = mean_flux - dark
    if signal <= 0:
        return DARK_LIMIT, mean_flux
    return m0 + ga - 2.5 * math.log10(signal), mean_flux


if __name__ == "__main__":
    M0, GA = -16.07, 28.02
    # One sample, no dark: same as the original single-reading formula.
    m, f = mpsas_from_samples([2.35e-3], M0, GA)
    assert abs(m - (M0 + GA - 2.5 * math.log10(2.35e-3))) < 1e-9 and f == 2.35e-3
    # Noisy samples around a faint level average to that level (4 counts +/- noise).
    cpu = 39124.0  # counts per uW/cm2 at max gain, 600 ms
    noisy = [c / cpu for c in (3, 5, 4, 6, 2, 4, 5, 3, 0, 8)]
    m, _ = mpsas_from_samples(noisy, M0, GA)
    assert abs(m - (M0 + GA - 2.5 * math.log10(4 / cpu))) < 1e-9
    # Negative samples are kept, not clipped.
    m, f = mpsas_from_samples([-1 / cpu, 3 / cpu], M0, GA)
    assert abs(f - 1 / cpu) < 1e-15 and m < DARK_LIMIT
    # Dark offset makes the sky read darker; all-dark reads the limit.
    assert mpsas_from_samples([4 / cpu], M0, GA, dark=2 / cpu)[0] > mpsas_from_samples([4 / cpu], M0, GA)[0]
    assert mpsas_from_samples([2 / cpu], M0, GA, dark=2 / cpu)[0] == DARK_LIMIT
    assert mpsas_from_samples([], M0, GA) == (DARK_LIMIT, 0.0)
    print("skycalc self-check passed")
