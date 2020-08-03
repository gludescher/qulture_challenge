
def test_always_passes():
    assert True

def test_always_fails():
    if 3 > 5:
        assert False
    else:
        assert True
        