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
        stories = self.get_sorted_story_name(reverse=False, include_base=True)
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
        if self.etabs.software == "ETABS":
            if auto_story and not all([bot_story_x, top_story_x, bot_story_y, top_story_y]):
                bot_story_x, top_story_x, bot_story_y, top_story_y = self.get_top_bot_stories()
            bot_level_x = self.get_elevation(bot_story_x)
            top_level_x = self.get_elevation(top_story_x)
            bot_level_y = self.get_elevation(bot_story_y)
            top_level_y = self.get_elevation(top_story_y)
        elif self.etabs.software == "SAP2000":
            bot_level_x, bot_level_y, _, top_level_x, top_level_y, _ = self.etabs.points.get_boundbox_coords()
        return bot_level_x, top_level_x, bot_level_y, top_level_y
    
    def get_elevation(self, story_name: str):
        return self.SapModel.Story.GetElevation(story_name)[0]

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
        if self.etabs.software == "ETABS":
            if bot_level_x is None:
                bot_level_x, top_level_x, bot_level_y, top_level_y = self.get_top_bot_levels()
            levels = self.SapModel.Story.GetStories()[2]
            no_of_x_story = len([i for i in levels if bot_level_x  <= i <= top_level_x])
            no_of_y_story = len([i for i in levels if bot_level_y  <= i <= top_level_y])
        elif self.etabs.software == "SAP2000":
            zs = self.etabs.points.get_unique_xyz_coordinates()[2]
            no_of_x_story = no_of_y_story = len(zs)
        return no_of_x_story - 1, no_of_y_story - 1

    def get_story_names(self):
        return self.SapModel.Story.GetNameList()[1]
    
    def get_sorted_story_and_levels(self,
                              reverse: bool=True,
                              include_base: bool=True,
                              ) -> list:
        '''
        return sorted story according to levels, if include_base it includes Base:
        [('Story1', level1), ('Story2', level2), ('Story3', level3), ... ]
        '''
        storyname_and_levels = self.storyname_and_levels()
        storyname_and_levels = sorted(storyname_and_levels.items(), key=lambda item: item[1], reverse=reverse)
        if not include_base:
            if reverse:
                storyname_and_levels = storyname_and_levels[:-1]
            else:
                storyname_and_levels = storyname_and_levels[1:]
        return storyname_and_levels
    
    def get_sorted_story_name(self,
                              reverse: bool=True,
                              include_base: bool=False,
                              ):
        storyname_and_levels = self.storyname_and_levels()
        stories = sorted(storyname_and_levels, key=storyname_and_levels.get, reverse=reverse)
        if not include_base:
            if reverse:
                stories = stories[:-1]
            else:
                stories = stories[1:]
        return stories
    
    def get_level_names(self):
        if self.etabs.software == "ETABS":
            return self.SapModel.Story.GetStories()[1]
        elif self.etabs.software == "SAP2000":
            zs = self.etabs.points.get_unique_xyz_coordinates()[2]
            level_names = [f"LEVEL{i}" for i in range(len(zs))]
            level_names[0] = "BASE"
            return level_names

    def get_base_name_and_level(self):
        name = self.SapModel.Story.GetStories()[1][0]
        level = self.SapModel.Story.GetStories()[2][0]
        return name, level
    
    def storyname_and_levels(self) -> dict:
        if self.etabs.software == "ETABS":
            stories_data = self.SapModel.Story.GetStories()
            names = stories_data[1]
            levels = stories_data[2]
        elif self.etabs.software == "SAP2000":
            levels = self.etabs.points.get_unique_xyz_coordinates()[2]
            names = [f"LEVEL{i}" for i in range(len(levels))]
            names[0] = "BASE"
        return dict(zip(names, levels))

    def get_story_boundbox(self, story_name, len_unit: str='cm') -> tuple:
        units = self.etabs.get_current_unit()
        if units[1] != len_unit:
            self.etabs.set_current_unit('kgf', len_unit)
        points = self.SapModel.PointObj.GetNameListOnStory(story_name)[1]
        if len(points) == 0:
            return (0, 0, 0, 0)
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
        if units[1] != len_unit:
            self.etabs.set_current_unit(*units)
        return x_min, y_min, x_max, y_max

    def get_stories_boundbox(self, len_unit: str='cm') -> dict:
        units = self.etabs.get_current_unit()
        self.etabs.set_current_unit('kgf', len_unit)
        stories = self.SapModel.Story.GetNameList()[1]
        stories_bb = {}
        for story in stories:
            bb = self.get_story_boundbox(story, len_unit=len_unit)
            stories_bb[story] = bb
        self.etabs.set_current_unit(*units)
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
            z = self.get_elevation(story)
            point_name = self.SapModel.PointObj.AddCartesian(float(x),float(y) , z)[0]  
            diaph = self.get_story_diaphragms(story).pop()
            self.SapModel.PointObj.SetDiaphragm(point_name, 3, diaph)
            story_point_in_center_of_rigidity[story] = point_name
        return story_point_in_center_of_rigidity

    def fix_below_stories(self, story_name):
        stories_name = self.SapModel.Story.GetNameList()[1]
        story_level = self.get_elevation(story_name)
        for name in stories_name:
            level = self.get_elevation(name)
            if level < story_level:
                points = self.SapModel.PointObj.GetNameListOnStory(name)[1]
                self.etabs.points.set_point_restraint(points)

    def get_diaphragm_force(self,
                            loadcases: list,
                            ):
        self.etabs.run_analysis()
        story_mass = self.etabs.database.get_story_mass_as_dict()
        story_forces = self.etabs.database.get_story_forces_of_loadcases(loadcases)
        stories = self.get_sorted_story_name(reverse=True, include_base=False)
        diaphragm_forces = dict.fromkeys(loadcases)
        cum_mass = 0
        cum_masses = {}
        for story in stories:
            mass = story_mass.get(story)
            cum_mass += mass
            cum_masses[story] = (cum_mass)
        for lc in loadcases:
            d = dict.fromkeys(stories)
            forces = story_forces.get(lc)
            for story, (vx, vy) in forces.items():
                mass = story_mass.get(story)
                cum_mass = cum_masses.get(story)
                fpx = vx * mass / cum_mass
                fpy = vy * mass / cum_mass
                d[story] = (fpx, fpy)
            diaphragm_forces[lc] = d
        return diaphragm_forces
    
    def get_diaphragm_earthquakes_factor(self,
                                         x_names: Union[list, None]=None,
                                         y_names: Union[list, None]=None,
                                         x_amplified_earthquakes: float=1,
                                         y_amplified_earthquakes: float=1,
                                         ai: float=0.35,
                            ):
        if x_names is None:
            x_names, y_names = self.etabs.load_patterns.get_xy_seismic_load_patterns_separate()
        all_loadcases = self.etabs.load_cases.get_load_cases()
        loadcases = list(x_names) + list(y_names)
        for lp in (loadcases):
            if lp not in all_loadcases:
                raise NameError(f"The loadcase '{lp}' did not exist in model. please check that loadpattern and loadcases have similar name.")
        self.etabs.run_analysis()
        story_mass = self.etabs.database.get_story_mass_as_dict(unit=('N', 'm'))
        story_forces = self.etabs.database.get_story_forces_of_loadcases(loadcases, unit=('N', 'm'))
        stories = self.get_sorted_story_name(reverse=True, include_base=False)
        diaphragm_earthquakes_factor = dict.fromkeys(loadcases)
        cum_mass = 0
        cum_masses = {}
        for story in stories:
            mass = story_mass.get(story) * 9.81
            cum_mass += mass
            cum_masses[story] = (cum_mass)
        for lp in x_names:
            d = dict.fromkeys(stories)
            forces = story_forces.get(lp)
            for story, (vx, vy) in forces.items():
                cum_mass = cum_masses.get(story)
                cp = vx / cum_mass
                cp = abs(cp)
                cp = max(0.5 * ai, cp)
                cp = min(cp, ai)
                d[story] = cp * x_amplified_earthquakes
            diaphragm_earthquakes_factor[lp] = d
        for lp in y_names:
            d = dict.fromkeys(stories)
            forces = story_forces.get(lp)
            for story, (vx, vy) in forces.items():
                cum_mass = cum_masses.get(story)
                cp = vy / cum_mass
                cp = abs(cp)
                cp = max(0.5 * ai, cp)
                cp = min(cp, ai)
                d[story] = cp * y_amplified_earthquakes
            diaphragm_earthquakes_factor[lp] = d
        return diaphragm_earthquakes_factor
    
    def create_files_diaphragm_applied_forces(self,
                                        stories: Union[list, None]=None,
                                        x_amplified_earthquakes: float=1,
                                        y_amplified_earthquakes: float=1,
                                        ai: float=0.35,
                                        d: dict={},
                                        folder_name: str='diaphragm_forces',
                                        ):
        '''
        ai: A * I
        '''
        diaphragm_earthquakes_factor = self.get_diaphragm_earthquakes_factor(
            ai=ai,
            x_amplified_earthquakes=x_amplified_earthquakes,
            y_amplified_earthquakes=y_amplified_earthquakes,
            )
        all_stories = self.get_sorted_story_name(reverse=True, include_base=True)
        if not d:
            d = self.etabs.get_settings_from_model()
        for story in stories:
            asli_file_path, _ = self.etabs.save_in_folder_and_add_name(
            folder_name = folder_name,
            name = story,
            )
            data = []
            for lc, story_factor in diaphragm_earthquakes_factor.items():
                factor = story_factor.get(story)
                i = all_stories.index(story)
                bot_story = all_stories[i + 1]
                c = str(factor)
                data.append(([lc], [story, bot_story, c, '1']))
            self.etabs.apply_cfactors_to_edb(data, d)
            self.SapModel.File.Save()
            self.SapModel.File.OpenFile(str(asli_file_path))
