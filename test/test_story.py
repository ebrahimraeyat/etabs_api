import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

@pytest.mark.getmethod
def test_get_heights():
    hx, hy = etabs.story.get_heights()
    h = 18.68
    assert hx == h
    assert hy == h

@pytest.mark.getmethod
def test_get_top_bot_stories():
    bot_story_x, top_story_x, bot_story_y, top_story_y = etabs.story.get_top_bot_stories()
    assert bot_story_x == bot_story_y == 'BASE'
    assert top_story_x == top_story_y == 'STORY5'

@pytest.mark.getmethod
def test_get_top_bot_levels():
    bot_level_x, top_level_x, bot_level_y, top_level_y = etabs.story.get_top_bot_levels()
    assert bot_level_x == bot_level_y == 0
    assert top_level_x == top_level_y == 18.68

@pytest.mark.getmethod
def test_get_no_of_stories():
    nx, ny = etabs.story.get_no_of_stories()
    assert nx == ny == 5
    nx, ny = etabs.story.get_no_of_stories(0, 15.84, 0, 15.84)
    assert nx == ny == 4

@pytest.mark.getmethod
def test_get_story_boundbox():
    geo = etabs.story.get_story_boundbox('STORY4')
    assert pytest.approx(geo, abs=.1) == (-118.1, 0, 1769, 1467.5)
    geo = etabs.story.get_story_boundbox('STORY5')
    assert pytest.approx(geo, abs=.1) == (653, 0, 1469, 500)

@pytest.mark.getmethod
def test_get_stories_boundbox():
    story_bb = etabs.story.get_stories_boundbox()
    assert len(story_bb) == 5
    bb = story_bb['STORY4']
    assert pytest.approx(bb, abs=.1) == (-118.1, 0, 1769, 1467.5)
    bb = story_bb['STORY5']
    assert pytest.approx(bb, abs=.1) == (653, 0, 1469, 500)

@pytest.mark.getmethod
def test_get_stories_length():
    story_length = etabs.story.get_stories_length()
    assert len(story_length) == 5
    length = story_length['STORY4']
    assert pytest.approx(length, abs=.1) == (1887.1, 1467.5)
    length = story_length['STORY5']
    assert pytest.approx(length, abs=.1) == (816, 500)

def test_get_story_diaphragms():
    diaph_set = set()
    for story in etabs.SapModel.Story.GetNameList()[1]:
        diaph = etabs.story.get_story_diaphragms(story).pop()
        diaph_set.add(diaph)
    assert diaph_set == {'D1'}

@pytest.mark.setmethod
def test_add_points_in_center_of_rigidity_and_assign_diph():
    story_point_in_center_of_rigidity = etabs.story.add_points_in_center_of_rigidity_and_assign_diph()
    assert len(story_point_in_center_of_rigidity) == 5

@pytest.mark.getmethod
def test_get_stories_diaphragms():
    story_diaphs = etabs.story.get_stories_diaphragms()
    assert story_diaphs == {
        'STORY5': ['D1'],
        'STORY4': ['D1'],
        'STORY3': ['D1'],
        'STORY2': ['D1'],
        'STORY1': ['D1'],
    }

def test_storyname_and_levels():
    etabs.set_current_unit('N', 'mm')
    story_levels = etabs.story.storyname_and_levels()
    assert story_levels == pytest.approx({
                    'BASE': 0.0, 
                    'STORY1': 5220.0, 
                    'STORY2': 8640.0, 
                    'STORY3': 12060.0, 
                    'STORY4': 15480.0, 
                    'STORY5': 18680.0,
                    })