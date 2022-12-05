import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_get_heights(shayesteh):
    hx, hy = shayesteh.story.get_heights()
    h = 18.68
    assert hx == h
    assert hy == h

@pytest.mark.getmethod
def test_get_top_bot_stories(shayesteh):
    bot_story_x, top_story_x, bot_story_y, top_story_y = shayesteh.story.get_top_bot_stories()
    assert bot_story_x == bot_story_y == 'BASE'
    assert top_story_x == top_story_y == 'STORY5'

@pytest.mark.getmethod
def test_get_top_bot_levels(shayesteh):
    bot_level_x, top_level_x, bot_level_y, top_level_y = shayesteh.story.get_top_bot_levels()
    assert bot_level_x == bot_level_y == 0
    assert top_level_x == top_level_y == 18.68

@pytest.mark.getmethod
def test_get_no_of_stories(shayesteh):
    nx, ny = shayesteh.story.get_no_of_stories()
    assert nx == ny == 5
    nx, ny = shayesteh.story.get_no_of_stories(0, 15.84, 0, 15.84)
    assert nx == ny == 4

@pytest.mark.getmethod
def test_get_story_boundbox(shayesteh):
    geo = shayesteh.story.get_story_boundbox('STORY4')
    assert pytest.approx(geo, abs=.1) == (-118.1, 0, 1769, 1467.5)
    geo = shayesteh.story.get_story_boundbox('STORY5')
    assert pytest.approx(geo, abs=.1) == (653, 0, 1469, 500)

@pytest.mark.getmethod
def test_get_stories_boundbox(shayesteh):
    story_bb = shayesteh.story.get_stories_boundbox()
    assert len(story_bb) == 5
    bb = story_bb['STORY4']
    assert pytest.approx(bb, abs=.1) == (-118.1, 0, 1769, 1467.5)
    bb = story_bb['STORY5']
    assert pytest.approx(bb, abs=.1) == (653, 0, 1469, 500)

@pytest.mark.getmethod
def test_get_stories_length(shayesteh):
    story_length = shayesteh.story.get_stories_length()
    assert len(story_length) == 5
    length = story_length['STORY4']
    assert pytest.approx(length, abs=.1) == (1887.1, 1467.5)
    length = story_length['STORY5']
    assert pytest.approx(length, abs=.1) == (816, 500)

def test_get_story_diaphragms(shayesteh):
    diaph_set = set()
    for story in shayesteh.SapModel.Story.GetNameList()[1]:
        diaph = shayesteh.story.get_story_diaphragms(story).pop()
        diaph_set.add(diaph)
    assert diaph_set == {'D1'}

@pytest.mark.setmethod
def test_add_points_in_center_of_rigidity_and_assign_diph(shayesteh):
    story_point_in_center_of_rigidity = shayesteh.story.add_points_in_center_of_rigidity_and_assign_diph()
    assert len(story_point_in_center_of_rigidity) == 5

@pytest.mark.getmethod
def test_get_stories_diaphragms(shayesteh):
    story_diaphs = shayesteh.story.get_stories_diaphragms()
    assert story_diaphs == {
        'STORY5': ['D1'],
        'STORY4': ['D1'],
        'STORY3': ['D1'],
        'STORY2': ['D1'],
        'STORY1': ['D1'],
    }