import tempfile
from pathlib import Path

import music21 as m21

import converter21


def _pickupScore() -> m21.stream.Score:
    # Two bars of 4/4 after a one-beat pickup, ending on a three-beat bar that completes it.
    part = m21.stream.Part()
    for number, (notes, padLeft, padRight) in enumerate([
        (['G4'], 3.0, 0.0),
        (['C5', 'B4', 'A4', 'G4'], 0.0, 0.0),
        (['F4', 'E4', 'D4'], 0.0, 1.0),
    ]):
        meas = m21.stream.Measure(number=number)
        if number == 0:
            meas.insert(0, m21.meter.TimeSignature('4/4'))
        for name in notes:
            meas.append(m21.note.Note(name, quarterLength=1.0))
        meas.paddingLeft = padLeft
        meas.paddingRight = padRight
        part.append(meas)
    return m21.stream.Score([part])


def test_a_pickup_and_its_completing_bar_survive_mei():
    converter21.register()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'pickup.mei'
        _pickupScore().write('mei', fp=path)
        written = path.read_text()
        assert written.count('metcon="false"') == 2
        back = m21.converter.parse(path, format='mei')
    measures = list(back.parts[0].getElementsByClass(m21.stream.Measure))
    assert measures[0].paddingLeft == 3.0
    assert measures[0].duration.quarterLength == 1.0
    assert measures[1].paddingLeft == 0 and measures[1].paddingRight == 0
    assert measures[-1].paddingRight == 1.0
    assert measures[-1].duration.quarterLength == 3.0


def test_a_full_bar_is_not_marked():
    converter21.register()
    score = _pickupScore()
    for meas in score.parts[0].getElementsByClass(m21.stream.Measure):
        meas.paddingLeft = meas.paddingRight = 0.0
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'nopickup.mei'
        score.write('mei', fp=path)
        assert 'metcon' not in path.read_text()
