from typing import Union

def get_beam_continuity(
                        beams_in_axis_plus_dimensions: list,
                        beams_in_axis_minus_dimensions: list,
                        bot_column_dimension: list,
                        axis: int=2, # local axis 2 or 3
):
    '''
    return continuity of beams in axis-2
    '''
    if min(len(beams_in_axis_minus_dimensions), len(beams_in_axis_plus_dimensions)) == 0:
        axis_continuity = False
    else:
        max_lenght_axis_minus = max([i[2] for i in beams_in_axis_minus_dimensions])
        max_height_axis_minus = max([i[1] for i in beams_in_axis_minus_dimensions])
        max_lenght_axis_plus = max([i[2] for i in beams_in_axis_plus_dimensions])
        max_height_axis_plus = max([i[1] for i in beams_in_axis_plus_dimensions])
        if max_lenght_axis_minus - (bot_column_dimension[axis - 2] / 2) > max_height_axis_plus:
            axis_minus_continuity = True
        else:
            axis_minus_continuity = False
        if max_lenght_axis_plus - (bot_column_dimension[axis - 2] / 2) > max_height_axis_minus:
            axis_plus_continuity = True
        else:
            axis_plus_continuity = False
        axis_continuity = axis_minus_continuity and axis_plus_continuity
    return axis_continuity

def get_column_continuity(
        bot_column_dimension: list,
        top_column_dimension: list,
) -> list:
    '''
    return continuity of column in axis-2 and axis-3
    '''
    top_column_height = top_column_dimension[2]
    return [top_column_height >= bot_column_dimension[i] for i in (0, 1)]

def get_joint_shear_vu_due_to_beams_mn_or_mpr(
    axis_plus_as_top: float,
    axis_plus_as_bot: float,
    axis_minus_as_top: float,
    axis_minus_as_bot: float,
    ductility: str='Intermediate',
    fy: float=400,
):
    phi = 1.0
    if ductility.lower() == "high":
        phi = 1.25
    as1 = axis_plus_as_top + axis_minus_as_bot
    as2 = axis_plus_as_bot + axis_minus_as_top
    vu1 = max(as1, as2) * phi * fy
    return vu1

def get_beam_section_mn(
        as_: float,
        d: float,
        fy: float,
        fc: float,
        width: float,
        ):
    rho = as_ / (width * d)
    mn = as_ * fy * d * (1 - .59 * rho * fy / fc)
    return mn

def get_beam_section_mpr(
        as_: float,
        d: float,
        fy: float,
        fc: float,
        width: float,
        ductility: str='Intermediate',
        ):
    phi = 1.0
    if ductility.lower() == "high":
        phi = 1.25
    rho = as_ / (width * d)
    mpr = as_ * phi * fy * d * (1 - .59 * rho * phi * fy / fc)
    return mpr

def get_vu_column_due_to_beams_mn_or_mpr(
        axis_plus_mn_top: float,
        axis_plus_mn_bot: float,
        axis_minus_mn_top: float,
        axis_minus_mn_bot: float,
        h_column_bot: float,
        h_column_top: float,
    ):
    mn1 = axis_plus_mn_top + axis_minus_mn_bot
    mn2 = axis_plus_mn_bot + axis_minus_mn_top
    hc = (h_column_bot + h_column_top) / 2
    vu_column = max(mn1, mn2) / hc
    return vu_column

def get_max_allowed_rebar_distance_due_to_crack_control(
        transver_rebar_size: int,
        fy: float=420,
        cover: float=40,
):
    fys = fy * 2 / 3
    cc = cover + transver_rebar_size
    ratio = 280 / fys
    allow_dist_1 = 380 * ratio - 2.5 * cc
    allow_dist_2 = 300 * ratio
    allow_dist = min(allow_dist_1, allow_dist_2)
    return allow_dist

def get_rebar_distance_in_section_width(
        section_width: float,
        rebar_size: int,
        number_of_rebars: int,
        transver_rebar_size: int,
        cover: float=40,
        net: bool=False,
):
    '''
    net: net distance or center to center
    '''
    cc = cover + transver_rebar_size
    n = 1
    if net:
        n = number_of_rebars
    distributed_length = section_width - (2 * cc + n * rebar_size)
    dist = distributed_length / (number_of_rebars - 1)
    return dist

def check_max_allowed_rebar_distance_due_to_crack_control(
        beam_width: float,
        rebar_size: int,
        number_of_rebars: int,
        transver_rebar_size: int,
        fy: float=420,
        cover: float=40,
):
    dist = get_rebar_distance_in_section_width(
        section_width=beam_width,
        rebar_size=rebar_size,
        number_of_rebars=number_of_rebars,
        transver_rebar_size=transver_rebar_size,
        cover=cover,
        net=False,
        )
    allow_dist = get_max_allowed_rebar_distance_due_to_crack_control(
        transver_rebar_size=transver_rebar_size,
        fy=fy,
        cover=cover,
    )
    result = dist <= allow_dist
    return result, dist, allow_dist

def control_mn_end_in_beam(
        as_top: float,
        as_bot: float,
        section_width: float,
        d_top: float,
        d_bot: Union[float, None]=None,
        fy: float=400,
        fc: float=30,
        ductility: str="Intermediate",
):
    if ductility.lower() == "high":
        factor = 1 / 2
    elif ductility.lower() == 'intermediate':
        factor = 1 / 3
    if d_bot is None:
        d_bot = d_top
    mn_top = get_beam_section_mn(as_=as_top, d=d_top, fy=fy, fc=fc, width=section_width)
    mn_bot = get_beam_section_mn(as_=as_bot, d=d_bot, fy=fy, fc=fc, width=section_width)
    ret = mn_bot >= factor * mn_top
    return ret, mn_top, mn_bot

def get_b_joint_shear_of_column(
    column_len_in_direction_of_investigate: float,
    column_len_perpendicular_of_investigate:float,
    beams_width: list,
    beams_c: list,
):
    b = sum(beams_width) / len(beams_width)
    c = sum(beams_c) / len(beams_c)
    b_joint_shear = min(column_len_in_direction_of_investigate, 2 * c) + b
    b_joint_shear = min(column_len_perpendicular_of_investigate, b_joint_shear)
    return b_joint_shear

    
    
    



