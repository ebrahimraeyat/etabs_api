

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

