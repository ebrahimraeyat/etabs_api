__all__ = ['Story']

from typing import Union


class Story:
    def __init__(
                self,
                SapModel=None,
                etabs=None,
                ):
        if not SapModel:
            self.etabs = etabs
            self.SapModel = etabs.SapModel
        else:
            self.SapModel = SapModel

    def get_top_bot_stories(self):
        '''
        return bot_x, top_x, bot_y, top_y stories name"
        '''
        stories = self.SapModel.Story.GetStories()[1]
        bot_story_x = bot_story_y = stories[0]
        top_story_x = top_story_y = stories[-1]
        return bot_story_x, top_story_x, bot_story_y, top_story_y

    def get_top_bot_levels(
                        self,
                        bot_story_x='',
                        top_story_x='',
                        bot_story_y='',
                        top_story_y='',
                        auto_story=True,
                        ):
        self.etabs.set_current_unit('kgf', 'm')
        if auto_story and not all([bot_story_x, top_story_x, bot_story_y, top_story_y]):
            bot_story_x, top_story_x, bot_story_y, top_story_y = self.get_top_bot_stories()
        bot_level_x = self.SapModel.Story.GetElevation(bot_story_x)[0]    
        top_level_x = self.SapModel.Story.GetElevation(top_story_x)[0]
        bot_level_y = self.SapModel.Story.GetElevation(bot_story_y)[0]    
        top_level_y = self.SapModel.Story.GetElevation(top_story_y)[0]
        return bot_level_x, top_level_x, bot_level_y, top_level_y

    def get_heights(
                    self,
                    bot_story_x='',
                    top_story_x='',
                    bot_story_y='',
                    top_story_y='',
                    auto_story=True,
                    ):
        bot_level_x, top_level_x, bot_level_y, top_level_y = self.get_top_bot_levels(
            bot_story_x, top_story_x, bot_story_y, top_story_y, auto_story)
        hx = top_level_x - bot_level_x
        hy = top_level_y - bot_level_y
        return hx, hy

    def get_no_of_stories(
                        self,
                        bot_level_x = None,
                        top_level_x = None,
                        bot_level_y = None,
                        top_level_y = None,
                        ):
        self.etabs.set_current_unit('kgf', 'm')
        if bot_level_x is None:
            bot_level_x, top_level_x, bot_level_y, top_level_y = self.get_top_bot_levels()
        levels = self.SapModel.Story.GetStories()[2]
        no_of_x_story = len([i for i in levels if bot_level_x  <= i <= top_level_x])
        no_of_y_story = len([i for i in levels if bot_level_y  <= i <= top_level_y])
        return no_of_x_story - 1, no_of_y_story - 1

    def get_story_names(self):
        return self.SapModel.Story.GetNameList()[1]
    
    def get_level_names(self):
        return self.SapModel.Story.GetStories()[1]

    def get_base_name_and_level(self):
        name = self.SapModel.Story.GetStories()[1][0]
        level = self.SapModel.Story.GetStories()[2][0]
        return name, level

    def get_story_boundbox(self, story_name) -> tuple:
        self.etabs.set_current_unit('kgf', 'cm')
        points = self.SapModel.PointObj.GetNameListOnStory(story_name)[1]
        xs = []
        ys = []
        for p in points:
            x, y, _, _ =  self.SapModel.PointObj.GetCoordCartesian(p)
            xs.append(x)
            ys.append(y)
        x_max = max(xs)
        x_min = min(xs)
        y_max = max(ys)
        y_min = min(ys)
        return x_min, y_min, x_max, y_max

    def get_stories_boundbox(self) -> dict:
        stories = self.SapModel.Story.GetNameList()[1]
        stories_bb = {}
        for story in stories:
            bb = self.get_story_boundbox(story)
            stories_bb[story] = bb
        return stories_bb

    def get_stories_length(self):
        story_bb = self.get_stories_boundbox()
        stories_length = {}
        for story, bb in story_bb.items():
            len_x = bb[2] - bb[0]
            len_y = bb[3] - bb[1]
            stories_length[story] = (len_x, len_y)
        return stories_length

    def get_story_diaphragms(self, story_name):
        '''
        Try to get Story diaphragm with point or area
        '''
        diaphs = set()
        areas = self.SapModel.AreaObj.GetNameListOnStory(story_name)[1]
        for area in areas:
            diaph = self.SapModel.AreaObj.GetDiaphragm(area)[0]
            if diaph != 'None':
                diaphs.add(diaph)
        points = self.SapModel.PointObj.GetNameListOnStory(story_name)[1]
        for point in points:
            diaph = self.SapModel.PointObj.GetDiaphragm(point)[1]
            if diaph:
                diaphs.add(diaph)
        return diaphs

    def get_stories_diaphragms(self,
        stories : Union[list, bool] = None,
        ):
        if stories is None:
            stories = self.get_story_names()
        story_diaphs = {}
        for story in stories:
            diaphs = self.get_story_diaphragms(story)
            story_diaphs[story] = list(diaphs)
        return story_diaphs


    # def disconnect_story_diaphragm(self, story_name):
    #     areas = self.SapModel.AreaObj.GetNameListOnStory(story_name)[1]
    #     for area in areas:
    #         self.SapModel.AreaObj.SetDiaphragm(area, 'None')
    #     points = self.SapModel.PointObj.GetNameListOnStory(story_name)[1]
    #     for point in points:
    #         self.SapModel.PointObj.SetDiaphragm(point, 1)

    # def assign_diaph_to_story_points(self, story_name, diaph):
    #     points = self.SapModel.PointObj.GetNameListOnStory(story_name)[1]
    #     for point in points:
    #         self.SapModel.PointObj.SetDiaphragm(point, 3, diaph)

    def add_points_in_center_of_rigidity_and_assign_diph(self):
        story_rigidity = self.etabs.database.get_center_of_rigidity()
        self.SapModel.SetModelIsLocked(False)
        story_point_in_center_of_rigidity = {}
        for story, (x, y) in story_rigidity.items():
            z = self.SapModel.story.GetElevation(story)[0]
            point_name = self.SapModel.PointObj.AddCartesian(float(x),float(y) , z)[0]  
            diaph = self.get_story_diaphragms(story).pop()
            self.SapModel.PointObj.SetDiaphragm(point_name, 3, diaph)
            story_point_in_center_of_rigidity[story] = point_name
        return story_point_in_center_of_rigidity

    def fix_below_stories(self, story_name):
        stories_name = self.SapModel.Story.GetNameList()[1]
        story_level = self.SapModel.Story.GetElevation(story_name)[0]
        for name in stories_name:
            level = self.SapModel.Story.GetElevation(name)[0]
            if level < story_level:
                points = self.SapModel.PointObj.GetNameListOnStory(name)[1]
                self.etabs.points.set_point_restraint(points)