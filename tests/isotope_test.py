"""Test isotope.py classes."""

from __future__ import print_function
import datetime
from dateutil.parser import parse as dateutil_parse
from six import string_types
import numpy as np
from becquerel.tools import element
from becquerel.tools import isotope
from becquerel import Spectrum
import pytest


TEST_ISOTOPES = [
    ('H-3', 'H', 3, ''),
    ('He-4', 'He', 4, ''),
    ('K-40', 'K', 40, ''),
    ('Co-60', 'Co', 60, ''),
    ('U-238', 'U', 238, ''),
    ('Pu-244', 'Pu', 244, ''),
    ('Tc-99m', 'Tc', 99, 'm'),
    ('Tc-99m', 'Tc', '99', 'm'),
    ('Tc-99m', 'Tc', 99, 1),
    ('Pa-234m', 'Pa', 234, 'm'),
    ('Hf-178m1', 'Hf', 178, 'm1'),
    ('Hf-178m2', 'Hf', 178, 'm2'),
    ('Hf-178m3', 'Hf', 178, 'm3'),
    ('Hf-178m3', 'Hf', 178, 3),
]


# ----------------------------------------------------
#                   Isotope class
# ----------------------------------------------------

@pytest.mark.parametrize('iso_str, sym, A, m', TEST_ISOTOPES)
def test_isotope_init_args(iso_str, sym, A, m):
    """Test Isotope init with 2 or 3 args, depending on whether m is None."""
    sym = str(sym)
    name = element.element_name(sym)
    Z = element.element_z(sym)
    A = int(A)
    elems = [
        sym, sym.lower(), sym.upper(),
        name, name.lower(), name.upper(),
        Z, str(Z)]
    mass_numbers = [A, str(A)]
    if isinstance(m, int):
        if m == 0:
            m = ''
        else:
            m = 'm{}'.format(m)
    if m == '':
        isomer_levels = [None, '', 0]
    elif m.lower() == 'm':
        isomer_levels = ['m', 'M', 1]
    elif m.lower() == 'm1':
        isomer_levels = ['m1', 'M1']
    else:
        isomer_levels = [m.lower(), m.upper(), int(m[1:])]
    for elem in elems:
        for mass in mass_numbers:
            for isomer in isomer_levels:
                args_list = [(elem, mass, isomer)]
                if isomer == '' or isomer is None:
                    args_list.append((elem, mass))
                for args in args_list:
                    print('')
                    print(args)
                    i = isotope.Isotope(*args)
                    print(i)
                    assert i.symbol == sym
                    assert i.A == A
                    assert i.m == m


@pytest.mark.parametrize('elem, A, m', [
    ('Xx', 45, ''),     # invalid element symbol
    (119, 250, ''),     # invalid Z (not in range 1..118)
    ('H', -1, ''),      # invalid A (negative)
    ('H', 'AA', ''),    # invalid A (string that cannot be converted to int)
    ('Ge', 30, ''),     # invalid N (negative)
    ('Tc', 99, 'n'),    # invalid m (does not start with 'm')
    ('Tc', 99, 'm-1'),  # invalid m (negative, str)
    ('Tc', 99, -1),     # invalid m (negative, int)
    ('Tc', 99, 1.0),    # invalid m (floating point)
])
def test_isotope_init_args_exceptions(elem, A, m):
    """Test Isotope init raises exceptions in some cases."""
    with pytest.raises(isotope.IsotopeError):
        isotope.Isotope(elem, A, m)


def test_isotope_init_args_exception_noargs():
    """Test Isotope init raises exception if no arguments given."""
    with pytest.raises(isotope.IsotopeError):
        isotope.Isotope()


def test_isotope_init_args_exception_1arg_nonstring():
    """Test Isotope init raises exception if one non-string argument given."""
    with pytest.raises(isotope.IsotopeError):
        isotope.Isotope(32)


def test_isotope_init_args_exception_4args():
    """Test Isotope init raises exception if four arguments given."""
    with pytest.raises(isotope.IsotopeError):
        isotope.Isotope('Tc', 99, 'm', 0)


@pytest.mark.parametrize('sym1, A1, m1, sym2, A2, m2, equal', [
    ('Tc', 99, '', 'Tc', 99, '', True),       # symbol and A only
    ('Tc', 99, 'm', 'Tc', 99, 'm', True),     # symbol, A, and m
    ('Hf', 178, 'm', 'Hf', 178, 'm1', True),  # m and m1 are equivalent
    ('Ge', 68, '', 'Ga', 68, '', False),      # symbols differ
    ('Ge', 68, '', 'Ge', 69, '', False),      # masses differ
    ('Ge', 68, '', 'Ge', 69, 'm', False),     # metastable states differ
    ('Ge', 68, 'm1', 'Ge', 69, 'm2', False),  # metastable states differ
])
def test_isotope_equality(sym1, A1, m1, sym2, A2, m2, equal):
    """Test Isotope equality and inequality."""
    i1 = isotope.Isotope(sym1, A1, m1)
    i2 = isotope.Isotope(sym2, A2, m2)
    if equal:
        assert i1 == i2
    else:
        assert i1 != i2


def test_isotope_equality_exception():
    """Test TypeError is raised when comparing an Isotope to a non-Isotope."""
    i1 = isotope.Isotope('Tc', 99, 'm')
    with pytest.raises(TypeError):
        assert i1 == 'Tc-99m'


@pytest.mark.parametrize('iso_str, sym, A, m', TEST_ISOTOPES)
def test_isotope_init_str(iso_str, sym, A, m):
    """Test Isotope init with one (string) argument.

    Isotope is identified by element symbol, A, and isomer number.

    Run tests for element symbol and name, in mixed case, upper case,
    and lower case.
    """
    sym = str(sym)
    mass_number = str(A)
    if m is not None:
        if isinstance(m, int):
            mass_number += 'm{}'.format(m)
        else:
            mass_number += m
    expected = isotope.Isotope(sym, A, m)
    for name in [sym, element.element_name(sym)]:
        iso_tests = [
            name + '-' + mass_number,
            name + mass_number,
            mass_number + '-' + name,
            mass_number + name,
        ]
        for iso in iso_tests:
            for iso2 in [iso, iso.upper(), iso.lower()]:
                print('')
                print('{}-{}: {}'.format(sym, mass_number, iso2))
                i = isotope.Isotope(iso2)
                print(i)
                assert i == expected


@pytest.mark.parametrize('iso_str, raises', [
    ('He_4', True),       # underscore
    ('He--4', True),      # hyphens
    ('4399', True),       # all numbers
    ('abdc', True),       # all letters
    ('Tc-99m3m', True),   # too many ms
    ('55mN', False),      # ambiguous but valid (returns Mn-55, not N-55m)
    ('55m2N', False),     # like previous but unambiguous (returns N-55m2)
    ('24Mg', False),      # unambiguous because G is not an element
    ('24m2G', True),      # like previous but invalid
    ('2He4', True),       # invalid mass number
    ('2He-4', True),      # invalid mass number
    ('He2-4', True),      # invalid mass number
    ('Xz-90', True),      # invalid element
    ('H-AA', True),       # invalid A (string that cannot be converted to int)
    ('H-20Xm1', True),    # invalid A (string that cannot be converted to int)
    ('Tc-99n', True),     # invalid m (does not start with 'm')
    ('Hf-178n3', True),   # invalid m (does not start with 'm')
    ('Tc-99m1.0', True),  # invalid m (floating point)
])
def test_isotope_init_str_exceptions(iso_str, raises):
    """Test Isotope init exceptions with one (string) argument."""
    if raises:
        with pytest.raises(isotope.IsotopeError):
            isotope.Isotope(iso_str)
    else:
        isotope.Isotope(iso_str)


@pytest.mark.parametrize('iso_str, sym, A, m', TEST_ISOTOPES)
def test_isotope_str(iso_str, sym, A, m):
    """Test Isotope.__str__()."""
    i = isotope.Isotope(sym, A, m)
    print(str(i), iso_str)
    assert str(i) == iso_str


# ----------------------------------------------------
#               IsotopeQuantity class
# ----------------------------------------------------

@pytest.fixture
def radioisotope():
    iso = isotope.Isotope('Cs-137')
    iso.halflife = 30.07 * 3.156e7
    iso.decay_const = np.log(2) / iso.halflife
    return iso


@pytest.fixture
def stable_isotope():
    iso = isotope.Isotope('Ca-40')
    iso.halflife = np.inf
    iso.decay_const = 0
    return iso


@pytest.fixture(params=[
    {'bq': 10.047 * isotope.UCI_TO_BQ},
    {'uci': 10.047},
    {'atoms': 1e24},
    {'g': 1e-5}
])
def iq_kwargs(request):
    return request.param


@pytest.fixture(params=[
    datetime.datetime.now(),
    '2015-01-08 00:00:00',
    None
])
def iq_date(request):
    return request.param


@pytest.mark.parametrize('iso', [
    radioisotope(),
    stable_isotope()
])
def test_isotopequantity_init(iso, iq_date, iq_kwargs):
    """Test IsotopeQuantity.__init__()"""

    if iso.decay_const == 0 and ('bq' in iq_kwargs or 'uci' in iq_kwargs):
        with pytest.raises(isotope.IsotopeError):
            iq = isotope.IsotopeQuantity(iso, date=iq_date, **iq_kwargs)
        return None
    iq = isotope.IsotopeQuantity(iso, date=iq_date, **iq_kwargs)
    assert iq.isotope is iso
    assert iq.halflife == iso.halflife
    assert iq.decay_const == iso.decay_const


def test_isotopequantity_ref_atoms_rad(radioisotope, iq_kwargs):
    """Test IsotopeQuantity.ref_atoms for a radioactive isotope"""

    iq = isotope.IsotopeQuantity(radioisotope, **iq_kwargs)
    if 'atoms' in iq_kwargs:
        assert iq.ref_atoms == iq_kwargs['atoms']
    elif 'g' in iq_kwargs:
        assert iq.ref_atoms == (
            iq_kwargs['g'] / radioisotope.A * isotope.N_AV)
    elif 'bq' in iq_kwargs:
        assert iq.ref_atoms == iq_kwargs['bq'] / radioisotope.decay_const
    else:
        assert iq.ref_atoms == (
            iq_kwargs['uci'] * isotope.UCI_TO_BQ / radioisotope.decay_const)


def test_isotopequantity_ref_atoms_stable(stable_isotope):
    """Test IsotopeQuantity.ref_atoms for a stable isotope"""

    atoms = 1e24
    iq = isotope.IsotopeQuantity(stable_isotope, atoms=atoms)
    assert iq.ref_atoms == atoms

    g = 1e-5
    iq = isotope.IsotopeQuantity(stable_isotope, g=g)
    assert iq.ref_atoms == g / stable_isotope.A * isotope.N_AV


@pytest.mark.parametrize('iso', [
    radioisotope(),
    stable_isotope()
])
def test_isotopequantity_ref_date(iso, iq_date):
    """Test IsotopeQuantity.ref_date"""

    iq = isotope.IsotopeQuantity(iso, date=iq_date, atoms=1e24)
    if isinstance(iq_date, datetime.datetime):
        assert iq.ref_date == iq_date
    elif isinstance(iq_date, string_types):
        assert iq.ref_date == dateutil_parse(iq_date)
    else:
        assert (datetime.datetime.now() - iq.ref_date).total_seconds() < 5


@pytest.mark.parametrize('iso, date, kwargs, error', [
    ('Cs-137', datetime.datetime.now(), {'uci': 10.047}, TypeError),
    (isotope.Isotope('Cs-137'), 123, {'bq': 456}, TypeError),
    (isotope.Isotope('Cs-137'), datetime.datetime.now(), {'asdf': 3},
     isotope.IsotopeError),
    (isotope.Isotope('Cs-137'), None, {'bq': -13.3}, ValueError)
])
def test_isotopequantity_bad_init(iso, date, kwargs, error):
    """Test errors from Isotope.__init__()"""

    if isinstance(iso, isotope.Isotope):
        iso.halflife = 3600
        iso.decay_const = np.log(2) / iso.halflife

    with pytest.raises(error):
        isotope.IsotopeQuantity(iso, date=date, **kwargs)


@pytest.fixture
def iq():
    """An IsotopeQuantity object"""

    iso = isotope.Isotope('Cs-137')
    iso.halflife = 30.07 * 3.156e7
    iso.decay_const = np.log(2) / iso.halflife
    date = datetime.datetime.now()
    kwargs = {'uci': 10.047}
    return isotope.IsotopeQuantity(iso, date=date, **kwargs)


@pytest.mark.parametrize('halflife', (3.156e7, 3600, 0.11))
def test_isotopequantity_at_methods(iq, halflife):
    """Test IsotopeQuantity.*_at()"""

    # since halflife is not built in to Isotope yet...
    iq.halflife = halflife
    iq.decay_const = np.log(2) / halflife
    iq.creation_date = False    # allow pre-refdate queries

    assert iq.atoms_at(iq.ref_date) == iq.ref_atoms
    assert iq.g_at(iq.ref_date) == iq.ref_atoms * iq.isotope.A / isotope.N_AV
    assert iq.bq_at(iq.ref_date) == iq.ref_atoms * iq.decay_const
    assert iq.uci_at(iq.ref_date) == (
        iq.ref_atoms * iq.decay_const / isotope.UCI_TO_BQ)

    dt = datetime.timedelta(seconds=halflife)
    assert iq.atoms_at(iq.ref_date + dt) == iq.ref_atoms / 2
    assert iq.atoms_at(iq.ref_date - dt) == iq.ref_atoms * 2

    dt = datetime.timedelta(seconds=halflife * 50)
    assert iq.bq_at(iq.ref_date + dt) / iq.bq_at(iq.ref_date) < 1e-12

    dt = datetime.timedelta(seconds=halflife / 100)
    assert np.isclose(
        iq.bq_at(iq.ref_date + dt), iq.bq_at(iq.ref_date), rtol=1e-2)


@pytest.mark.parametrize('kw', ('atoms', 'g', 'bq', 'uci'))
@pytest.mark.parametrize('halflife', (3.156e7, 3600, 0.11))
def test_isotopequantity_time_when(iq, kw, halflife):
    """Test IsotopeQuantity.time_when()"""

    iq.halflife = halflife
    iq.creation_date = False

    ref_qty = getattr(iq, kw + '_at')(iq.ref_date)

    kwarg = {kw: ref_qty}
    assert iq.time_when(**kwarg) == iq.ref_date

    d = iq.ref_date - datetime.timedelta(seconds=halflife)
    kwarg = {kw: ref_qty * 2}
    assert iq.time_when(**kwarg) == d

    d = iq.ref_date + datetime.timedelta(seconds=halflife)
    kwarg = {kw: ref_qty / 2}
    assert iq.time_when(**kwarg) == d


def test_isotopequantity_time_when_error(stable_isotope):
    """Test error for time_when on a stable isotope"""

    iq = isotope.IsotopeQuantity(stable_isotope, g=10)
    with pytest.raises(isotope.IsotopeError):
        iq.time_when(g=5)


def test_isotopequantity_creation_date(radioisotope):
    """Test IsotopeQuantity created or non-created at ref date"""

    iq = isotope.IsotopeQuantity(
        radioisotope, date='2017-01-01 00:00:00', bq=1, creation_date=True)
    with pytest.raises(isotope.IsotopeError):
        iq.atoms_at('2016-01-01 00:00:00')
    assert iq.time_when(atoms=iq.ref_atoms + 10) is None
    iq.atoms_at('2017-01-02 00:00:00')
    iq.time_when(atoms=iq.ref_atoms - 10)

    iq = isotope.IsotopeQuantity(
        radioisotope, date='2017-01-01 00:00:00', bq=1, creation_date=False)
    iq.atoms_at('2016-01-01 00:00:00')
    assert iq.time_when(atoms=iq.ref_atoms + 10) is not None
    iq.atoms_at('2017-01-02 00:00:00')
    iq.time_when(atoms=iq.ref_atoms - 10)

    # default True
    iq = isotope.IsotopeQuantity(
        radioisotope, date='2017-01-01 00:00:00', bq=1)
    with pytest.raises(isotope.IsotopeError):
        iq.atoms_at('2016-01-01 00:00:00')
    assert iq.time_when(atoms=iq.ref_atoms + 10) is None
    iq.atoms_at('2017-01-02 00:00:00')
    iq.time_when(atoms=iq.ref_atoms - 10)


def test_isotopequantity_activity_now(iq):
    """Test IsotopeQuantity.*_now()"""

    # since halflife is not built in to Isotope yet...
    iq.halflife = 3600

    assert np.isclose(iq.bq_now(), iq.bq_at(datetime.datetime.now()))
    assert np.isclose(iq.uci_now(), iq.uci_at(datetime.datetime.now()))
    assert np.isclose(iq.atoms_now(), iq.atoms_at(datetime.datetime.now()))
    assert np.isclose(iq.g_now(), iq.g_at(datetime.datetime.now()))


def test_isotopequantity_decays_from(iq):
    """Test IsotopeQuantity.*_from()"""

    t0 = datetime.datetime.now()
    # since halflife is not built in to Isotope yet...
    th = 3600
    iq.halflife = th
    dt = datetime.timedelta(seconds=th)

    t1 = t0 + dt
    t2 = t1 + dt

    assert np.isclose(iq.decays_from(t0, t1), iq.atoms_at(t1))
    assert np.isclose(iq.decays_from(t1, t2), iq.atoms_at(t2))
    assert np.isclose(iq.decays_from(t0, t2), 3 * iq.atoms_at(t2))

    assert np.isclose(iq.bq_from(t0, t1), iq.atoms_at(t1) / th)

    assert np.isclose(
        iq.uci_from(t0, t1), iq.atoms_at(t1) / th / isotope.UCI_TO_BQ)


def test_isotopequantity_decays_during(iq):
    """Test IsotopeQuantity.*_during()"""

    dt_s = iq.halflife
    t0 = datetime.datetime.now()
    t1 = t0 + datetime.timedelta(seconds=dt_s)
    spec = Spectrum(np.zeros(256), start_time=t0, stop_time=t1)

    assert np.isclose(iq.decays_during(spec), iq.atoms_now() / 2)
    assert np.isclose(iq.bq_during(spec), iq.decays_during(spec) / dt_s)
    assert np.isclose(iq.uci_during(spec),
                      iq.bq_during(spec) / isotope.UCI_TO_BQ)


# ----------------------------------------------------
#               NeutronIrradiation class
# ----------------------------------------------------

@pytest.mark.parametrize('start, stop, n_cm2, n_cm2_s', [
    ('2017-01-01 00:00:00', '2017-01-01 12:00:00', None, 1e12),
    ('2017-01-01 00:00:00', '2017-01-01 12:00:00', 1e15, None),
    ('2017-01-01 00:00:00', '2017-01-01 00:00:00', 1e15, None)
])
def test_irradiation_init(start, stop, n_cm2, n_cm2_s):
    """Test valid inits for NeutronIrradiation"""

    ni = isotope.NeutronIrradiation(start, stop, n_cm2=n_cm2, n_cm2_s=n_cm2_s)
    assert hasattr(ni, 'n_cm2')


@pytest.mark.parametrize('start, stop, n_cm2, n_cm2_s, error', [
    ('2017-01-01 00:00:00', '2017-01-01 12:00:00', 1e15, 1e12, ValueError),
    ('2017-01-01 12:00:00', '2017-01-01 00:00:00', None, 1e12, ValueError)
])
def test_irradiation_bad_init(start, stop, n_cm2, n_cm2_s, error):
    """Test invalid inits for NeutronIrradiation"""

    with pytest.raises(error):
        isotope.NeutronIrradiation(start, stop, n_cm2=n_cm2, n_cm2_s=n_cm2_s)


def test_irradiation_activate_forward_pulse():
    """Test NeutronIrradiation.activate() for forward calculation"""

    start = datetime.datetime.now()
    stop = start
    n_cm2 = 1e15

    iso0 = isotope.Isotope('Cs-133')
    iso0.halflife = np.inf
    iso0.decay_const = 0
    barns = 1

    iso1 = isotope.Isotope('Cs-134')
    iso1.halflife = 2 * 3.156e7
    iso1.decay_const = np.log(2) / iso1.halflife

    iq0 = isotope.IsotopeQuantity(iso0, date=start, atoms=1e24)

    ni = isotope.NeutronIrradiation(start, stop, n_cm2=n_cm2)
    iq1 = ni.activate(barns, initial_iso_q=iq0, activated_iso=iso1)
    assert iq1.ref_date == stop
    assert np.isclose(iq1.ref_atoms, n_cm2 * barns * 1e-24 * iso0.ref_atoms)
