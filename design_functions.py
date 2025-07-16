from pathlib import Path
import math
from typing import Union
from dataclasses import dataclass

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

import python_functions

# from steelas.member.member import SteelSection, SteelMember
# from steelas.data.io import MemberLibrary


def get_overwrites_of_frames(
                            overwrites_csv_file: Union[Path, str],
                            frames: list,
                                ) -> pd.DataFrame:
    '''
    Get a csv file that contains the frame overwrites and a list of frame names.
    if each value of frame names is various, return various in Value column, otherwise return 
    unique value
    '''
    df = pd.read_csv(overwrites_csv_file)
    if len(df.columns) > 3: # There is saved overwrites of some frames
        current_frame_names = df.columns[3:]  # Get columns from the 4th column onwards
        relevant_columns = current_frame_names.intersection(frames)
        if len(relevant_columns) > 0:
            results = []

            for index, row in df.iterrows():
                values = row[relevant_columns].values
                unique_values = set(values)
                options = row['Options']
                if len(unique_values) == 1:
                    new_value = unique_values.pop()
                    # results.append([row['Item'], new_value, options])
                else:
                    new_value = "various"
                    if new_value not in options:
                        options = options + f',{new_value}'
                results.append([row['Item'], new_value, options])
            df = pd.DataFrame(results, columns=['Item', 'Value', 'Options'])
    return df

def save_overwrites_of_frames(
                              updated_df,
                              original_df,
                              relevant_columns,
                              overwrites_csv_file=None,
                              ):
    if len(original_df.columns) > 3:
        current_frames = original_df.columns[3:]
        new_frames = list(set(relevant_columns).difference(current_frames))
    for index, row in updated_df.iterrows():
        if row['Value'] == "various":
            # If the user has modified it, we keep it as is (do nothing)
            if len(original_df.columns) == 3:
                continue
            if len(new_frames) > 0:
                original_df.loc[index, new_frames] = original_df['Value'][index]
        else:
            # Update original DataFrame with the new value
            original_df.loc[index, relevant_columns] = row['Value']
    if overwrites_csv_file and Path(overwrites_csv_file).parent.exists():
        original_df.to_csv(overwrites_csv_file, index=False)
    return original_df

def get_point_and_bounds_restraints(restraints):
    """

    Parameters:
    restraints (list): A list containing floats and bounding restraints (tuples of two floats).

    Returns:
    list: A list of floats and bounding restraints.
    """
    restraints = set(restraints)
    floats = []
    bounds = []
    
    # Separate floats and bounds
    for restraint in restraints:
        sup = restraint[0]
        if isinstance(sup, (tuple, list)) and len(sup) == 2:
            bounds.append(restraint)
        else:
            floats.append(restraint)
    return floats, bounds

class Section:
    pass


@dataclass
class PointRestraint:
    name: Union[str, None]
    location: float
    flange_restraints: str
    x_values: list
    m_values: list
    m_func: Union[interp1d, None] = None
    critical_flang: Union[str, None] = None
    cf_restraint: Union[str, None] = None
    moment_sign: Union[str, None] = None
    start_of_bounding_restraint: bool = False
    rotationally_restrained: bool = False
    middle_of_bounding_restraint: bool = False
    end_of_bounding_restraint: bool = False
    toleranc: float = .001

    def __post_init__(self):
        if self.m_func is None:
            self.m_func = interp1d(self.x_values, self.m_values, kind=1, fill_value='extrapolate')
        if self.moment_sign is None:
            self.moment_sign = self.get_moment_sign()
        if self.critical_flang is None:
            self.critical_flang = self.get_critical_flang()
        if self.cf_restraint is None:
            self.cf_restraint = self.get_critical_flang_restraint()
        self.moment_value = self.get_moment_value()

    def __str__(self):
        return f"{self.name}, {self.location}, {self.flange_restraints}, {self.critical_flang}, {self.cf_restraint}"
    
    def __repr__(self):
        return self.__str__()
    
    def get_moment_value(self, x_value=None):
        if self.m_func is None:
            raise ValueError
        if x_value is None:
            x_value = self.location
        return self.m_func(x_value)
    
    def get_moment_sign(self):
        moment = self.m_func(self.location)
        sign = python_functions.get_sign_of_value(moment, tol=self.toleranc)
        if self.location == self.x_values[0]:
            m_epsilon = self.get_moment_value(self.location + 100 * self.toleranc)
            sign_epsilon = python_functions.get_sign_of_value(m_epsilon, tol=self.toleranc)
            return f"{sign}{sign_epsilon}"
        
        elif self.location == self.x_values[-1]:
            m_epsilon = self.get_moment_value(self.location - 100 * self.toleranc)
            sign_epsilon = python_functions.get_sign_of_value(m_epsilon, tol=self.toleranc)
            return f"{sign}{sign_epsilon}"
        else:
            if sign == '0' and self.middle_of_bounding_restraint:
                a = self.location - 100 * self.toleranc
                if a > self.x_values[0]:
                    moment = self.get_moment_value(a)
                    tol_sign = python_functions.get_sign_of_value(moment, tol=self.toleranc)
                    sign = tol_sign + sign
                b = self.location + 100 * self.toleranc
                if b < self.x_values[-1]:
                    moment = self.get_moment_value(b)
                    tol_sign = python_functions.get_sign_of_value(moment, tol=self.toleranc)
                    sign += tol_sign
            return sign
    
    def get_critical_flang(self):
        if self.moment_sign is None:
            raise ValueError
        if self.moment_sign in  ('-', '-0', '0-', '--'):
            return 'Botton'
        elif self.moment_sign in ('+', '+0', '0+', '++'):
            return 'Top'
        elif self.moment_sign in ('-0+', '+0-'):
            return 'Either'
        elif self.moment_sign in ('0', '00'):
            return 'Both'
        
    def get_critical_flang_restraint(self):
        if self.critical_flang is None:
            raise ValueError
        if self.critical_flang == 'Botton':
            restraint = self.flange_restraints[1]
        elif self.critical_flang == 'Top':
            restraint = self.flange_restraints[0]
        elif self.critical_flang == 'Both':
            if 'U' in self.flange_restraints:
                restraint = 'U'
            elif 'P' in self.flange_restraints:
                restraint = 'P'
            elif 'L' in self.flange_restraints:
                restraint = 'L'
            elif 'F' in self.flange_restraints:
                restraint = 'F'
        elif self.critical_flang == 'Either':
            if 'F' in self.flange_restraints:
                restraint = 'F'
            elif 'L' in self.flange_restraints:
                restraint = 'L'
            elif 'P' in self.flange_restraints:
                restraint = 'P'
            elif 'U' in self.flange_restraints:
                restraint = 'U'
        if (self.location == self.x_values[0] or self.location == self.x_values[-1]) and \
        restraint in ('PLF'):
            restraint = 'F'
        return restraint

@dataclass    
class Segment:
    start_restraint: PointRestraint
    end_restraint: PointRestraint
    restraints: Union[str, None] = None
    name: Union[str, None] = None
    length: Union[float, None] = None
    kr: Union[float, None] = None
    kt: Union[float, None] = None
    kl: Union[float, None] = None
    alpha_m: Union[float, None] = None
    le: Union[float, None] = None

    def __post_init__(self):
        if self.name is None:
            self.name = f"{self.start_restraint.name}-{self.end_restraint.name}"
        if self.restraints is None:
            self.restraints = self.start_restraint.cf_restraint + self.end_restraint.cf_restraint
        if self.length is None:
            self.length = self.get_length()
        if self.kr is None:
            self.kr = self.get_kr()
        if self.kt is None:
            self.kt = self.get_kt()
        if self.kl is None:
            self.kl = self.get_kl()
        if self.alpha_m is None:
            self.alpha_m = self.get_alpha_m()
        if self.le is None:
            self.le = self.get_effective_length()

    def __str__(self):
        return f"'{self.name}', '{self.restraints}', ({self.start_restraint.location}, {self.end_restraint.location})"
    
    def __repr__(self):
        return self.__str__()
    
    def get_length(self):
        return self.end_restraint.location - self.start_restraint.location
    
    def get_kr(self):
        if self.restraints in ('FU', 'PU') or \
            (self.restraints in ('FF', 'FP', 'FL', 'PP', 'PL', 'LL') and \
            not (self.start_restraint.rotationally_restrained or self.end_restraint.rotationally_restrained)
            ):
            return 1
        elif self.restraints in ('FF', 'FP', 'PP') and \
        (self.start_restraint.rotationally_restrained or self.end_restraint.rotationally_restrained):
            return 0.85
        elif self.restraints in ('FF', 'FP', 'PP') and \
        (self.start_restraint.rotationally_restrained and self.end_restraint.rotationally_restrained):
            return 0.7
        return 1.0
    
    def get_kt(self):
        return 1
    
    def get_kl(self):
        return 1.0
        
    def get_alpha_m(self):
        start = self.start_restraint.location
        end = self.end_restraint.location
        dx = (self.length) / 4
        x_values = [start] + [start + i * dx for i in (1, 2, 3)] + [end]
        m_values = self.start_restraint.m_func(x_values)
        m_values = [abs(m_value) for m_value in m_values]
        m_max = max(m_values)
        m_2, m_3, m_4 = m_values[1:-1]
        return 1.7 * m_max / math.sqrt(m_2 ** 2 + m_3 ** 2 + m_4 ** 2)
    
    def get_effective_length(self):
        return self.length * self.kt * self.kl*  self.kr
        

@dataclass
class Beam:
    name: str
    length: float
    section: Section
    section_type: str
    section_catergory: str
    intermediate_restraints: list
    start_support: str
    end_support: str
    load_combinations_values : dict
    is_composite: bool = False
    ignore_d: bool = False
    segments: Union[dict, None] = None
    x_values: Union[np.array, None] = None
    tolerance: float = 1

    def __post_init__(self):
        if self.x_values is None:
            self.x_values = list(self.load_combinations_values.values())[0][0]
        if self.is_composite:
            self.add_composite_restraint()
        if self.segments is None:
            self.segments = self.get_segments()

    def add_composite_restraint(self):
        start = self.x_values[0]
        end = self.x_values[-1]
        if self.ignore_d:
            start += 1.5 * self.section.geom.d
            end -= 1.5 * self.section.geom.d
        self.intermediate_restraints.append(((start, end), 'LU'))

    def get_segments(self):
        combo_segments = dict()
        for combo, (x_values, m_values) in self.load_combinations_values.items():
            segments = get_segments_of_frame(
                self.intermediate_restraints,
                x_values,
                m_values,
                self.start_support,
                self.end_support,
                self.tolerance,
            )
            combo_segments[combo] = segments
        return combo_segments


def convert_bounding_restraints_to_point_restraints(
        bounds_restraints: list,
        x_values: list,
        m_values: list,
        tolerance: float = .001,
        ):
    """
    Regarding with moment value, find the root of moment value, if this moment values
    are in any bounding restraint, it add point restraint at that point

    bounds_restraints: list of bound_restraints
    """
    z = python_functions.find_roots(x_values, m_values)
    m_func = interp1d(x_values, m_values, kind=1, fill_value='extrapolate')
    points_restraints = []
    for bound_restraints in bounds_restraints:
        point_restraints = []
        for bs in bound_restraints:
            (start, end), restraint = bs
            for x_value in z:
                if start < x_value < end:
                    point_restraints.append(PointRestraint(None, x_value, restraint, x_values, m_values, m_func, middle_of_bounding_restraint=True, toleranc=tolerance))
            point_restraints.append(PointRestraint(None, start, restraint, x_values, m_values, m_func, start_of_bounding_restraint=True, toleranc=tolerance))
            point_restraints.append(PointRestraint(None, end, restraint, x_values, m_values, m_func, end_of_bounding_restraint=True, toleranc=tolerance))
        points_restraints.append(point_restraints)
    return points_restraints

def convert_beam_restraints_to_points(
        restraints: list,
        x_values: list,
        m_values: list,
        tolerance: float = 0.001,
        ):
    '''
    Get top and buttom restraint of beam, include points and bounds restraints
    and convert to point restraints for top and buttom of beam regarding 
    moment values of beam
    '''
    points, bounds = get_point_and_bounds_restraints(restraints)
    bounds_point_restraints = convert_bounding_restraints_to_point_restraints(
        [bounds], x_values, m_values, tolerance=tolerance,
    )
    point_restraints = []
    for point in points:
        pr = PointRestraint(None, point[0], point[1], x_values, m_values, toleranc=tolerance)
        point_restraints.append(pr)
    point_restraints = sorted(
        point_restraints + bounds_point_restraints[0],
        key= lambda x: x.location)
    return point_restraints, bounds

def get_beam_point_restraints_with_respect_to_supports_and_remove_duplicates(
        point_restraints,
        start_support,
        end_support,
        x_values,
        m_values,
        tolerance: float = 0.001,
        ):
    if isinstance(start_support, (tuple, list)):
        start_support = PointRestraint('A', start_support[0], start_support[1], x_values, m_values, toleranc=tolerance)
    if isinstance(end_support, (tuple, list)):
        end_support = PointRestraint('B', end_support[0], end_support[1], x_values, m_values, toleranc=tolerance)
    if len(point_restraints) > 0 and isinstance(point_restraints[0], (tuple, list)):
        point_restraints = [PointRestraint(None, p[0], p[1], x_values, m_values, toleranc=tolerance) for p in point_restraints]
    # else:
    #     point_restraints = []

    point_restraints = [start_support, end_support] + point_restraints
    results = []
    repeat = []

    for i, x_restraint in enumerate(point_restraints):
        if i not in repeat:
            for j, y_restraint in enumerate(point_restraints[i + 1:]):
                if math.isclose(x_restraint.location, y_restraint.location):
                    repeat.append(j + i + 1)
            results.append(x_restraint)
    point_restraints = sorted(results, key= lambda x: x.location)
    return point_restraints

def get_segments_of_frame(
        restraints: list,
        x_values: list,
        m_values: list,
        start_support: str= 'FF',
        end_support: str= 'FF',
        tolerance: float = 0.001,
        ):
    point_restraints, bounds_restraints = convert_beam_restraints_to_points(restraints, x_values, m_values, tolerance=tolerance)
    point_restraints = get_beam_point_restraints_with_respect_to_supports_and_remove_duplicates(
        point_restraints,
        (x_values[0], start_support),
        (x_values[-1], end_support),
        x_values=x_values,
        m_values=m_values,
        tolerance=tolerance,
    )
    segments = []
    # start_restraint = point_restraints[0]
    # start_restraint.name = 'A'
    # for i, p_restraint in enumerate(point_restraints[1:], start=1):
    #     if i == len(point_restraints):
    #         p_restraint.name = 'B'
    #     else:
    #         p_restraint.name = str(i)
    #     if p_restraint.cf_restraint != 'U':




    interp_func = interp1d(x_values, m_values, kind=1, fill_value='extrapolate')
    # m_values_at_restraints = interp_func([x.location for x in point_restraints])
    segment_start_restraint = point_restraints[0]
    n = 1 # segment number
    for i, restraint in enumerate(point_restraints[1:], start=-1):
        i += 1
        if i != len(point_restraints) - 2:
            restraint.name = str(i + 1)
        found_bound_restraint_that_res_a_and_res_b_is_in_it = False
        x_center = (segment_start_restraint.location + restraint.location) / 2
        m_center = interp_func(x_center)
        for brs in bounds_restraints:
            (xb_a, xb_b), (rsb_top, rsb_bot) = brs
            if (xb_a <= segment_start_restraint.location <= xb_b) and (xb_a <= restraint.location <= xb_b): # segment is within bound restraint
                if (m_center > 0 and rsb_top !='U') or (m_center < 0 and rsb_bot != 'U'): # full restraint segments
                    found_bound_restraint_that_res_a_and_res_b_is_in_it = True
                    n += 1
                    segment_start_restraint = restraint
                    break
        if not found_bound_restraint_that_res_a_and_res_b_is_in_it:
            # segment_restraint = get_segment_restraint(
            #     segment_start_restraint,
            #     restraint,
            #     m_values_at_restraints[i],
            #     m_values_at_restraints[i + 1],
            #     m_center,
            #     )
            # if segment_restraint is not None:
            if restraint.cf_restraint != "U":
                segments.append(Segment(segment_start_restraint, restraint))
                n += 1
                segment_start_restraint = restraint
    return segments

# def filter_and_sort_restraints(restraints):
#     """
#     Filters and sorts a list of floats and bounding restraints.

#     Parameters:
#     restraints (list): A list containing floats and bounding restraints (tuples of two floats).

#     Returns:
#     list: A sorted list of floats and bounding restraint, with floats within any bounding range removed.
#     """
#     restraints = set(restraints)
#     top_floats = []
#     top_bounds = []
#     bot_floats = []
#     bot_bounds = []
    
#     # Separate floats and bounds
#     for restraint in restraints:
#         sup, (top, bot) = restraint
#         if isinstance(sup, (tuple, list)) and len(sup) == 2:
#             if top.upper() != 'U':
#                 top_bounds.append((sup, top))
#             if bot.upper() != 'U':
#                 bot_bounds.append((sup, bot))
#         else:
#             if top.upper() != 'U':
#                 top_floats.append((sup, top))
#             if bot.upper() != 'U':
#                 bot_floats.append((sup, bot))
#     # Combine overlapping bounds
#     combined_top_bounds = []
#     for b in sorted(top_bounds, key=lambda x: x[0][0]):
#         if len(combined_top_bounds) > 0:
#             cb_1 = combined_top_bounds[-1]
#         if not combined_top_bounds or cb_1[0][1] < b[0][0]:
#             combined_top_bounds.append(b)
#         else:
#             combined_top_bounds[-1] = ((cb_1[0][0], max(cb_1[0][1], b[0][1])), cb_1[1])
#     combined_bot_bounds = []
#     for b in sorted(bot_bounds, key=lambda x: x[0][0]):
#         if len(combined_bot_bounds) > 0:
#             cb_1 = combined_bot_bounds[-1]
#         if not combined_bot_bounds or cb_1[0][1] < b[0][0]:
#             combined_bot_bounds.append(b)
#         else:
#             combined_bot_bounds[-1] = ((cb_1[0][0], max(cb_1[0][1], b[0][1])), cb_1[1])

#     # Filter out floats that are within any bounding range
#     filtered_top_floats = []
#     for f in top_floats:
#         if not any(b[0][0] <= f[0] <= b[0][1] for b in combined_top_bounds):
#             filtered_top_floats.append(f)
#     filtered_bot_floats = []
#     for f in bot_floats:
#         if not any(b[0][0] <= f[0] <= b[0][1] for b in combined_bot_bounds):
#             filtered_bot_floats.append(f)

#     # Combine filtered floats and combined bounds
#     combined_top_list = filtered_top_floats + combined_top_bounds
#     sorted_combined_top = sorted(combined_top_list, key=lambda x: x[0][0] if isinstance(x[0], (list, tuple)) else x[0])
#     combined_bot_list = filtered_bot_floats + combined_bot_bounds
#     sorted_combined_bot = sorted(combined_bot_list, key=lambda x: x[0][0] if isinstance(x[0], (list, tuple)) else x[0])
#     return sorted_combined_top, sorted_combined_bot