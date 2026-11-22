import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import music21 as m21

import converter21

MEI = '{http://www.music-encoding.org/ns/mei}'


def _score(staves: int, voices: bool) -> m21.stream.Score:
    # 6/4, a bar of 9/4, then 6/4 again, on each staff.
    parts = []
    for _ in range(staves):
        part = m21.stream.Part()
        for number, sig in enumerate(['6/4', '9/4', '6/4'], start=1):
            meas = m21.stream.Measure(number=number)
            meas.insert(0, m21.meter.TimeSignature(sig))
            beats = int(sig.split('/')[0])
            if voices:
                for name in ('C5', 'E4'):
                    v = m21.stream.Voice()
                    for _ in range(beats):
                        v.append(m21.note.Note(name, quarterLength=1.0))
                    meas.insert(0, v)
            else:
                for _ in range(beats):
                    meas.append(m21.note.Note('C5', quarterLength=1.0))
            part.append(meas)
        parts.append(part)
    return m21.stream.Score(parts)


def _check(score: m21.stream.Score, staves: int):
    converter21.register()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'meter.mei'
        score.write('mei', fp=path)
        root = ET.parse(path).getroot()
        back = m21.converter.parse(path, format='mei')
    for m in root.iter(f'{MEI}measure'):
        assert not list(m.iter(f'{MEI}staffDef')) and not list(m.iter(f'{MEI}scoreDef'))
        assert not list(m.iter(f'{MEI}meterSig'))
    section = root.find(f'.//{MEI}section')
    kids = [(e.tag[len(MEI):], e.get('n') or e.get('meter.count')) for e in section]
    assert kids == [('measure', '1'), ('scoreDef', '9'), ('measure', '2'),
                    ('scoreDef', '6'), ('measure', '3')]
    assert len(back.parts) == staves
    for part in back.parts:
        sigs = [(ts.measureNumber, ts.ratioString)
                for ts in part.recurse().getElementsByClass(m21.meter.TimeSignature)]
        assert sigs == [(1, '6/4'), (2, '9/4'), (3, '6/4')]


def test_a_meter_change_on_voiced_staves_is_one_scoredef_between_measures():
    _check(_score(2, voices=True), 2)


def test_a_meter_change_on_a_melody_alone_is_one_scoredef_between_measures():
    _check(_score(1, voices=False), 1)
