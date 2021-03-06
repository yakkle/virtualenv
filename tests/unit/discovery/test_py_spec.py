from __future__ import absolute_import, unicode_literals

import itertools
import os
import sys
from copy import copy

import pytest

from virtualenv.discovery.py_spec import PythonSpec


def test_bad_py_spec():
    text = "python2.3.4.5"
    spec = PythonSpec.from_string_spec(text)
    assert text in repr(spec)
    assert spec.str_spec == text
    assert spec.path == os.path.abspath(text)
    content = vars(spec)
    del content[str("str_spec")]
    del content[str("path")]
    assert all(v is None for v in content.values())


def test_py_spec_first_digit_only_major():
    spec = PythonSpec.from_string_spec("278")
    assert spec.major == 2
    assert spec.minor == 78


def test_spec_satisfies_path_ok():
    spec = PythonSpec.from_string_spec(sys.executable)
    assert spec.satisfies(spec) is True


def test_spec_satisfies_path_nok(tmp_path):
    spec = PythonSpec.from_string_spec(sys.executable)
    of = PythonSpec.from_string_spec(str(tmp_path))
    assert spec.satisfies(of) is False


def test_spec_satisfies_arch():
    spec_1 = PythonSpec.from_string_spec("python-32")
    spec_2 = PythonSpec.from_string_spec("python-64")

    assert spec_1.satisfies(spec_1) is True
    assert spec_2.satisfies(spec_1) is False


@pytest.mark.parametrize(
    "req, spec",
    list(itertools.combinations(["py", "CPython", "python"], 2)) + [("jython", "jython")] + [("CPython", "cpython")],
)
def test_spec_satisfies_implementation_ok(req, spec):
    spec_1 = PythonSpec.from_string_spec(req)
    spec_2 = PythonSpec.from_string_spec(spec)
    assert spec_1.satisfies(spec_1) is True
    assert spec_2.satisfies(spec_1) is True


def test_spec_satisfies_implementation_nok():
    spec_1 = PythonSpec.from_string_spec("python")
    spec_2 = PythonSpec.from_string_spec("jython")
    assert spec_2.satisfies(spec_1) is False
    assert spec_1.satisfies(spec_2) is False


def _version_satisfies_pairs():
    target = set()
    version = tuple(str(i) for i in sys.version_info[0:3])
    for i in range(len(version) + 1):
        req = ".".join(version[0:i])
        for j in range(i + 1):
            sat = ".".join(version[0:j])
            # can be satisfied in both directions
            target.add((req, sat))
            target.add((sat, req))
    return sorted(target)


@pytest.mark.parametrize("req, spec", _version_satisfies_pairs())
def test_version_satisfies_ok(req, spec):
    req_spec = PythonSpec.from_string_spec("python{}".format(req))
    sat_spec = PythonSpec.from_string_spec("python{}".format(spec))
    assert sat_spec.satisfies(req_spec) is True


def _version_not_satisfies_pairs():
    target = set()
    version = tuple(str(i) for i in sys.version_info[0:3])
    for i in range(len(version)):
        req = ".".join(version[0 : i + 1])
        for j in range(i + 1):
            sat_ver = list(sys.version_info[0 : j + 1])
            for l in range(j + 1):
                for o in [1, -1]:
                    temp = copy(sat_ver)
                    temp[l] += o
                    sat = ".".join(str(i) for i in temp)
                    target.add((req, sat))
    return sorted(target)


@pytest.mark.parametrize("req, spec", _version_not_satisfies_pairs())
def test_version_satisfies_nok(req, spec):
    req_spec = PythonSpec.from_string_spec("python{}".format(req))
    sat_spec = PythonSpec.from_string_spec("python{}".format(spec))
    assert sat_spec.satisfies(req_spec) is False


def test_relative_spec(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    a_relative_path = str((tmp_path / "a" / "b").relative_to(tmp_path))
    spec = PythonSpec.from_string_spec(a_relative_path)
    assert spec.path == os.path.abspath(str(tmp_path / a_relative_path))
