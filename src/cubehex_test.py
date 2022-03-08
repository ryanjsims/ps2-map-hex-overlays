from typing import Tuple
from drawing import CubeHex, Map

def within_pct(percent: float, a: Tuple, b: Tuple):
    for el1, el2 in zip(a, b):
        if not abs((el1 - el2) / el2) < (percent / 100.0):
            return False
    return True

ERROR_PCT = 0.1

def test_oshur():
    assert within_pct(ERROR_PCT, CubeHex(  0,   0,   0).to_world(True), (-  29.0, -  50))
    assert within_pct(ERROR_PCT, CubeHex(-25,   4,  21).to_world(True), (- 374.6, -2350))
    assert within_pct(ERROR_PCT, CubeHex( 22, -15, - 7).to_world(True), ( 1270.0,  1400))
    assert within_pct(ERROR_PCT, CubeHex( 31, -31,   0).to_world(True), ( 2653.0,  1500))
    assert within_pct(ERROR_PCT, CubeHex(- 8, -20,  28).to_world(True), ( 1701.0, -1850))
    assert within_pct(ERROR_PCT, CubeHex(- 4,  26, -22).to_world(True), (-2278.6,   850))

def test_indar():
    assert within_pct(ERROR_PCT, CubeHex(  0,   0,   0).to_world(), (-  57.75, - 100))
    assert within_pct(ERROR_PCT, CubeHex(-11,   5,   6).to_world(), (- 923.50, -1800))
    assert within_pct(ERROR_PCT, CubeHex( 20, -15, - 5).to_world(), ( 2537.50,  2400))
    assert within_pct(ERROR_PCT, CubeHex(- 6, -15,  21).to_world(), ( 2537.50, -2800))
    assert within_pct(ERROR_PCT, CubeHex(- 1, -15,  16).to_world(), ( 2537.50, -1800))
