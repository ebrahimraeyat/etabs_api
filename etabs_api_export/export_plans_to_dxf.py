import math
import string
import random
from pathlib import Path
from typing import List, Iterable, Union

import numpy as np
import matplotlib.pyplot as plt

import ezdxf

# try:
#     from docx.shared import Inches
# except ImportError:
#     import freecad_funcs
#     package = 'python-docx'
#     freecad_funcs.install_package(package)


etabs_api_path = Path(__file__).absolute().parent.parent


def add_lines_to_dxf(
        line_coords: List,
        block,
        dxfattribs: dict={},
        insertion: tuple=(0, 0),
        ):
    '''
    line_coords format : [([x1, y1], [x2, y2]), ...]
    '''
    x, y = insertion
    for p1, p2 in line_coords:
        block.add_line((p1[0] + x, p1[1] + y), (p2[0] + x, p2[1] + y), dxfattribs=dxfattribs)
    return block
               

def add_rectangles_to_dxf(
        rectangle_coords: List,
        block,
        dxfattribs: dict={},
        insertion: tuple=(0, 0),
        
        ):
    '''
    rectangle_coords format : [([x1, y1], [x2, y2], [x3, y3], [x4, y4]), ...]
    '''
    x, y = insertion
    for p1, p2 in zip(rectangle_coords[:-1], rectangle_coords[1:]):
        block.add_line((p1[0] + x, p1[1] + y), (p2[0] + x, p2[1] + y), dxfattribs=dxfattribs)
    return block

def convert_5point_to_8point(cx_, cy_, w_, h_, a_):
    theta = math.radians(-a_)
    bbox = np.array([[cx_], [cy_]]) + \
        np.matmul([[math.cos(theta), math.sin(theta)],
                   [-math.sin(theta), math.cos(theta)]],
                  [[-w_ / 2, w_/ 2, w_ / 2, -w_ / 2],
                   [-h_ / 2, -h_ / 2, h_ / 2, h_ / 2]])
    polygon = [[bbox[0][i], bbox[1][i]] for i in range(4)]
    return polygon

def get_beam_columns_coords(etabs, story):
    beam_columns = etabs.frame_obj.get_beams_columns_on_stories()
    beams, columns = beam_columns[story]
    beam_coords = []
    for name in beams:
        x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
        beam_coords.append(([x1, x2], [y1, y2]))
    polygons = []
    for name in columns:
        x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
        rotation = etabs.SapModel.FrameObj.GetLocalAxes(name)[0]
        polygon = convert_5point_to_8point(x1, y1, 50, 50, a_=rotation)
        polygons.append(polygon)
    return beam_coords, polygons

# def get_beam_column_dxf(
#         etabs,
#         beam_name: str,
#         ) -> Path:
#     '''
#     Get the axes of beams and columns of story that beam_name belogs to
#     '''
#     # Get beam, columns coordinates
#     beam_coords, column_polygons = get_beam_columns_coords(etabs, beam_name)
    
#     add_lines_to_dxf(beam_coords, )
#     add_rectangles_to_dxf(column_polygons)
#     set_ax_boundbox(ax, etabs, beam_name)
#     return fig, ax


# def set_ax_boundbox(ax, etabs, story, scale=1, bb_add=120):
#     units = etabs.get_current_unit()
#     x_min, y_min, x_max, y_max = etabs.story.get_story_boundbox(story, len_unit=units[1])
#     ax.set_xlim((x_min - bb_add) * scale, (x_max + bb_add) * scale)
#     ax.set_ylim((y_min - bb_add) * scale, (y_max + bb_add) * scale)

def export_to_dxf(
        etabs,
        filename,
        Open_file: bool=False,
        draw_offset_beam: bool = False,
):
    dxf_temp = etabs_api_path / "etabs_api_export" / "templates" / "dxf" / "TEMPLATE_PLANS_OF_STORIES.dxf"
    dwg = ezdxf.readfile(dxf_temp)
    msp = dwg.modelspace()
    etabs.set_current_unit('kgf', 'm')
    beam_columns = etabs.frame_obj.get_beams_columns_on_stories()
    dx = 0
    for story, level in etabs.story.storyname_and_levels().items():
        ret = beam_columns.get(story, None)
        if ret is None:
            continue
        beams, columns = ret
        frame_props = etabs.frame_obj.get_section_type_and_geometry(beams)
        block_name = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        block = dwg.blocks.new(name=block_name)
        for name in beams:
            props = frame_props.get(name)
            if props:
                b = props.get('b', 0)
            else:
                b = 0
            x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
            # Draw center line
            block.add_line((x1 + dx, y1), (x2 + dx, y2), dxfattribs = {'color': 8})
            if draw_offset_beam and b: # add offset lines
                offset = b / 2
                x1_offset, y1_offset, x2_offset, y2_offset = etabs.frame_obj.offset_frame_points(x1, y1, x2, y2, offset, neg=True)
                block.add_line((x1_offset + dx, y1_offset), (x2_offset + dx, y2_offset), dxfattribs = {'color': 2})
                x1_offset, y1_offset, x2_offset, y2_offset = etabs.frame_obj.offset_frame_points(x1, y1, x2, y2, offset, neg=False)
                block.add_line((x1_offset + dx, y1_offset), (x2_offset + dx, y2_offset), dxfattribs = {'color': 2})
            section_name = etabs.frame_obj.get_section_name(name)
            xc = (x1 + x2) / 2
            yc = (y1 + y2) / 2
            mtext = block.add_mtext(section_name, dxfattribs = {'color': 3, 'style': 'ROMANT'})
            mtext.set_location(insert=(xc + dx, yc - 0.05), attachment_point=2)
            if (x2 - x1) == 0:
                rotation = 90
            else:
                rotation = math.degrees(math.atan((y2 - y1) / (x2 - x1)))
            mtext.dxf.rotation = rotation
            mtext.dxf.char_height = .12
        frame_props = etabs.frame_obj.get_section_type_and_geometry(columns)
        for name in columns:
            x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
            rotation = etabs.SapModel.FrameObj.GetLocalAxes(name)[0]
            props = frame_props.get(name)
            b = props.get('b', .5)
            d = props.get('d', .5)
            polygon = convert_5point_to_8point(x1, y1, b, d, a_=rotation - 90)
            for p1, p2 in zip(polygon, polygon[1:] + [polygon[0]]):
                block.add_line((p1[0] + dx, p1[1]), (p2[0] + dx, p2[1]), dxfattribs = {'color': 3})
        xmin, ymin, xmax, ymax = etabs.story.get_story_boundbox(story, len_unit='m')
        block.add_text(f"Elevation: {int(level * 100)}", dxfattribs={'height': .30, 'style': 'ROMANT'}).set_pos((dx + (xmax - xmin) / 2, ymin - 1))
        dx += xmax * 1.2
        msp.add_blockref(block_name, (0 , 0))
    dwg.saveas(filename)
    if Open_file:
        from python_functions import open_file
        open_file(filename=filename)

def export_to_dxf_beam_rebars(
        etabs,
        filename,
        Open_file: bool=False,
        top_rebars: str='3~16',
        bot_rebars: str='3~16',
        torsion_rebar: str='1~20',
        frame_names: Union[Iterable, None]=None,
        moment_redistribution_positive_coefficient: float=1.1,
        moment_redistribution_negative_coefficient: float=0.9,

):
    dxf_temp = etabs_api_path / "etabs_api_export" / "templates" / "dxf" / "TEMPLATE_PLANS_OF_STORIES.dxf"
    dwg = ezdxf.readfile(dxf_temp)
    msp = dwg.modelspace()
    etabs.set_current_unit('kgf', 'm')
    beam_columns = etabs.frame_obj.get_beams_columns_on_stories()
    x_coeff = 0.1
    block_dx = 0
    etabs.start_design(check_designed=True)
    top_rebars_areas = 0
    for t in top_rebars.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        top_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    bot_rebars_areas = 0
    for t in bot_rebars.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        bot_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    torsion_rebars_areas = 0
    for t in torsion_rebar.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        torsion_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    print(f"{top_rebars}={top_rebars_areas}, {bot_rebars}={bot_rebars_areas}, {torsion_rebar}={torsion_rebars_areas}")
    for story, level in etabs.story.storyname_and_levels().items():
        ret = beam_columns.get(story, None)
        if ret is None:
            continue
        beams, columns = ret
        # if frame_names is not None:
        #     beams = set(beams).intersection(frame_names)
        if len(beams) == 0:
            continue
        block_name = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        block = dwg.blocks.new(name=block_name)
        for name in beams:
            x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
            length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            # Draw center line
            block.add_line((x1 + block_dx, y1), (x2 + block_dx, y2), dxfattribs = {'color': 8})
            if name in frame_names:
                try:
                    ret = etabs.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
                except IndexError:
                    continue
                print(f"processing beam {name=}")
                abs_dy = .02 * length
                n = ret[0]
                if n % 2:
                    i =  j = int(n / 2) + 1
                else:
                    i = int(n / 2)
                    j = i + 1
                # start rebars
                start_ta = ret[4][0]
                start_ba = ret[6][0]
                start_lt = ret[10][0] / 2
                torsion_rebars_area = min(start_lt, torsion_rebars_areas)
                # if start_lt == 0:
                #     torsion_rebars_area = 0
                # else:
                #     torsion_rebars_area = torsion_rebars_areas
                additional_start_ta = start_ta * moment_redistribution_negative_coefficient - top_rebars_areas + start_lt - torsion_rebars_area
                additional_start_ba = start_ba - bot_rebars_areas + start_lt - torsion_rebars_area
                # end rebars
                end_ta = ret[4][-1]
                end_ba = ret[6][-1]
                end_lt = ret[10][-1] / 2
                torsion_rebars_area = min(end_lt, torsion_rebars_areas)
                # if end_lt == 0:
                #     torsion_rebars_area = 0
                # else:
                #     torsion_rebars_area = torsion_rebars_areas
                additional_end_ta = end_ta * moment_redistribution_negative_coefficient - top_rebars_areas + end_lt - torsion_rebars_area
                additional_end_ba = end_ba - bot_rebars_areas + end_lt - torsion_rebars_area
                # midle rebars
                if n < 3:
                    additional_mid_ta = 0
                    additional_mid_ba = 0
                else:
                    mid_ta = (ret[4][i] + ret[4][j]) / 2
                    mid_ba = (ret[6][i] + ret[6][j]) / 2
                    mid_lt = (ret[10][i] + ret[10][j]) / 2 / 2
                    torsion_rebars_area = min(mid_lt, torsion_rebars_areas)
                    # if mid_lt == 0:
                    #     torsion_rebars_area = 0
                    # else:
                    #     torsion_rebars_area = torsion_rebars_areas
                    additional_mid_ta = mid_ta - top_rebars_areas + mid_lt - torsion_rebars_area
                    additional_mid_ba = mid_ba * moment_redistribution_positive_coefficient - bot_rebars_areas + mid_lt - torsion_rebars_area
                xc = (x1 + x2) / 2
                yc = (y1 + y2) / 2
                alpha_start = math.atan(abs_dy / (x_coeff * length))
                alpha_mid = math.atan(abs_dy / (0.5 * length))
                alpha_end = math.atan(abs_dy / ((1 - x_coeff) * length))
                if (x2 - x1) == 0:
                    rotation = math.radians(90)
                else:
                    rotation = math.atan((y2 - y1) / (x2 - x1))
                for x, y, areas, alpha in zip((x1, x1, x1), (y1, y1, y1), 
                                    (
                                        (additional_start_ta, additional_start_ba),
                                        (additional_mid_ta, additional_mid_ba),
                                        (additional_end_ta, additional_end_ba),
                                        ),
                                        (alpha_start, alpha_mid, alpha_end),
                                        ):
                    for area, loc, sign in zip(areas, ('T', 'B'), (1, -1)):
                        area *= 10000
                        if area > 0.2 or area < -.5:
                            color = 3
                            if area < 0:
                                color = 8
                            r = abs(abs_dy / math.sin(alpha))
                            teta_alph = rotation + sign * alpha
                            dx = r * math.cos(teta_alph)
                            dy = r * math.sin(teta_alph)
                            mtext = block.add_mtext(f"{loc}={area:.2f}", dxfattribs = {'color': color, 'style': 'ROMANT'})
                            mtext.set_location(insert=(x + dx + block_dx, y + dy), attachment_point=5)
                            mtext.dxf.rotation = math.degrees(rotation)
                            mtext.dxf.char_height = .013 * length
        # frame_props = etabs.frame_obj.get_section_type_and_geometry(columns)
        # for name in columns:
        #     x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
        #     rotation = etabs.SapModel.FrameObj.GetLocalAxes(name)[0]
        #     props = frame_props.get(name)
        #     b = props.get('b', .5)
        #     d = props.get('d', .5)
        #     polygon = convert_5point_to_8point(x1, y1, b, d, a_=rotation - 90)
        #     for p1, p2 in zip(polygon, polygon[1:] + [polygon[0]]):
        #         block.add_line((p1[0] + dx, p1[1]), (p2[0] + dx, p2[1]), dxfattribs = {'color': 3})
        xmin, ymin, xmax, ymax = etabs.story.get_story_boundbox(story, len_unit='m')
        block.add_text(f"Elevation: {int(level * 100)}", dxfattribs={'height': .30, 'style': 'ROMANT'}).set_pos((block_dx + (xmax - xmin) / 2, ymin - 1))
        block_dx += xmax * 1.2
        msp.add_blockref(block_name, (0 , 0))
    dwg.saveas(filename)
    if Open_file:
        from python_functions import open_file
        open_file(filename=filename)

def export_to_image_beam_rebars(
        etabs,
        filename,
        Open_file: bool=False,
        top_rebars: str='3~16',
        bot_rebars: str='3~16',
        torsion_rebar: str='1~20',
        frame_names: Union[Iterable, None]=None,
        figsize: tuple=(12, 8),
        font_size: int=12,
):
    etabs.set_current_unit('kgf', 'm')
    beam_columns = etabs.frame_obj.get_beams_columns_on_stories()
    x_coeff = 0.1
    abs_dy = .2
    etabs.start_design(check_designed=True)
    top_rebars_areas = 0

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = {'beam': 'black', 'top': 'blue', 'bot': 'red', 'text': 'green'}

    for t in top_rebars.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        top_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    bot_rebars_areas = 0
    for t in bot_rebars.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        bot_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    torsion_rebars_areas = 0
    for t in torsion_rebar.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        torsion_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    print(f"{top_rebars}={top_rebars_areas}, {bot_rebars}={bot_rebars_areas}, {torsion_rebar}={torsion_rebars_areas}")
    for story, level in etabs.story.storyname_and_levels().items():
        ret = beam_columns.get(story, None)
        if ret is None:
            continue
        beams, columns = ret
        if frame_names is not None:
            beams = set(beams).intersection(frame_names)
        if len(beams) == 0:
            continue
        for name in beams:
            x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
            length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if (x2 - x1) == 0:
                rotation = 90
            else:
                rotation = math.degrees(math.atan((y2 - y1) / (x2 - x1)))
            # Draw center line
            ax.plot([x1, x2], [y1, y2], color=colors['beam'], linewidth=2)
            if frame_names and name in frame_names:
                ret = etabs.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
                n = ret[0]
                if n % 2:
                    i =  j = int(n / 2) + 1
                else:
                    i = int(n / 2)
                    j = i + 1
                # start rebars
                start_ta = ret[4][0]
                start_ba = ret[6][0]
                start_lt = ret[10][0] / 2
                if start_lt == 0:
                    torsion_rebars_area = 0
                else:
                    torsion_rebars_area = torsion_rebars_areas
                additional_start_ta = start_ta * 0.9 - top_rebars_areas + start_lt - torsion_rebars_area
                additional_start_ba = start_ba - bot_rebars_areas + start_lt - torsion_rebars_area
                # end rebars
                end_ta = ret[4][-1]
                end_ba = ret[6][-1]
                end_lt = ret[10][-1] / 2
                if end_lt == 0:
                    torsion_rebars_area = 0
                else:
                    torsion_rebars_area = torsion_rebars_areas
                additional_end_ta = end_ta * 0.9 - top_rebars_areas + end_lt - torsion_rebars_area
                additional_end_ba = end_ba - bot_rebars_areas + end_lt - torsion_rebars_area
                # midle rebars
                mid_ta = (ret[4][i] + ret[4][j]) / 2
                mid_ba = (ret[6][i] + ret[6][j]) / 2
                mid_lt = (ret[10][i] + ret[10][j]) / 2 / 2
                if mid_lt == 0:
                    torsion_rebars_area = 0
                else:
                    torsion_rebars_area = torsion_rebars_areas
                additional_mid_ta = mid_ta - top_rebars_areas + mid_lt - torsion_rebars_area
                additional_mid_ba = mid_ba * 1.1 - bot_rebars_areas + mid_lt - torsion_rebars_area
                xc = (x1 + x2) / 2
                yc = (y1 + y2) / 2
                alpha_start = math.degrees(math.atan(abs_dy / (x_coeff * length)))
                alpha_mid = math.degrees(math.atan(abs_dy / (0.9 * length)))
                alpha_end = math.degrees(math.atan(abs_dy / ((1 - x_coeff) * length)))
                for x, y, areas, alpha in zip((x1, xc, x2), (y1, yc, y2), 
                                    (
                                        (additional_start_ta, additional_start_ba),
                                        (additional_mid_ta, additional_mid_ba),
                                        (additional_end_ta, additional_end_ba),
                                        ),
                                        (alpha_start, alpha_mid, alpha_end),
                                        ):
                    for area, loc, sign in zip(areas, ('T', 'B'), (1, -1)):
                        area *= 10000
                        if area > 0.5 or area < -.5:
                            color = 'blue'
                            if area < 0:
                                color = 'red'
                            r = abs_dy / math.sin(alpha)
                            dx = r * math.cos(rotation + sign * alpha)
                            dy = r * math.sin(rotation + sign * alpha)
                            ax.text(x+dx, y+dy, f"{loc}:{area:.2f}", color=color, fontsize=font_size, rotation=rotation, va='center', ha='center')
        # frame_props = etabs.frame_obj.get_section_type_and_geometry(columns)
        # for name in columns:
        #     x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
        #     rotation = etabs.SapModel.FrameObj.GetLocalAxes(name)[0]
        #     props = frame_props.get(name)
        #     b = props.get('b', .5)
        #     d = props.get('d', .5)
        #     polygon = convert_5point_to_8point(x1, y1, b, d, a_=rotation - 90)
        #     for p1, p2 in zip(polygon, polygon[1:] + [polygon[0]]):
        #         block.add_line((p1[0] + dx, p1[1]), (p2[0] + dx, p2[1]), dxfattribs = {'color': 3})
    ax.set_aspect('equal')
    ax.set_title("Beam Rebars Layout")
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=300)
    else:
        plt.show()
    if Open_file:
        from python_functions import open_file
        open_file(filename=filename)


def export_to_image_beam_rebars_pyqtgraph(
        etabs,
        filename,
        Open_file: bool=False,
        top_rebars: str='3~16',
        bot_rebars: str='3~16',
        torsion_rebar: str='1~20',
        frame_names: Union[Iterable, None]=None,
        figsize: tuple=(12, 8),
        font_size: int=12,
):
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtWidgets
    import numpy as np
    
    # Create application and window
    app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(size=figsize)
    win.setWindowTitle("Beam Rebars Layout")
    
    # Create plot item
    plot = win.addPlot(title="Beam Rebars Layout")
    plot.setAspectLocked(True)  # Equivalent to ax.set_aspect('equal')
    etabs.set_current_unit('kgf', 'm')
    beam_columns = etabs.frame_obj.get_beams_columns_on_stories()
    x_coeff = 0.1
    abs_dy = .2
    etabs.start_design(check_designed=True)
    top_rebars_areas = 0

    colors = {'beam': 'yellow', 'top': 'blue', 'bot': 'red', 'text': 'green'}

    for t in top_rebars.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        top_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    bot_rebars_areas = 0
    for t in bot_rebars.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        bot_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    torsion_rebars_areas = 0
    for t in torsion_rebar.split('+'):
        n, diameter = t.split('~')
        n, diameter = int(n), int(diameter)
        torsion_rebars_areas += n * math.pi * (diameter / 1000) ** 2 / 4
    print(f"{top_rebars}={top_rebars_areas}, {bot_rebars}={bot_rebars_areas}, {torsion_rebar}={torsion_rebars_areas}")
    for story, level in etabs.story.storyname_and_levels().items():
        ret = beam_columns.get(story, None)
        if ret is None:
            continue
        beams, columns = ret
        if frame_names is not None:
            beams = set(beams).intersection(frame_names)
        if len(beams) == 0:
            continue
        for name in beams:
            x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
            length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if (x2 - x1) == 0:
                rotation = 90
            else:
                rotation = math.degrees(math.atan((y2 - y1) / (x2 - x1)))
            # Draw center line
            plot.plot([x1, x2], [y1, y2], pen=pg.mkPen(color=colors['beam'], width=2))
            # ax.plot([x1, x2], [y1, y2], color=colors['beam'], linewidth=2)
            if frame_names and name in frame_names:
                ret = etabs.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
                n = ret[0]
                if n % 2:
                    i =  j = int(n / 2) + 1
                else:
                    i = int(n / 2)
                    j = i + 1
                # start rebars
                start_ta = ret[4][0]
                start_ba = ret[6][0]
                start_lt = ret[10][0] / 2
                if start_lt == 0:
                    torsion_rebars_area = 0
                else:
                    torsion_rebars_area = torsion_rebars_areas
                additional_start_ta = start_ta * 0.9 - top_rebars_areas + start_lt - torsion_rebars_area
                additional_start_ba = start_ba - bot_rebars_areas + start_lt - torsion_rebars_area
                # end rebars
                end_ta = ret[4][-1]
                end_ba = ret[6][-1]
                end_lt = ret[10][-1] / 2
                if end_lt == 0:
                    torsion_rebars_area = 0
                else:
                    torsion_rebars_area = torsion_rebars_areas
                additional_end_ta = end_ta * 0.9 - top_rebars_areas + end_lt - torsion_rebars_area
                additional_end_ba = end_ba - bot_rebars_areas + end_lt - torsion_rebars_area
                # midle rebars
                mid_ta = (ret[4][i] + ret[4][j]) / 2
                mid_ba = (ret[6][i] + ret[6][j]) / 2
                mid_lt = (ret[10][i] + ret[10][j]) / 2 / 2
                if mid_lt == 0:
                    torsion_rebars_area = 0
                else:
                    torsion_rebars_area = torsion_rebars_areas
                additional_mid_ta = mid_ta - top_rebars_areas + mid_lt - torsion_rebars_area
                additional_mid_ba = mid_ba * 1.1 - bot_rebars_areas + mid_lt - torsion_rebars_area
                xc = (x1 + x2) / 2
                yc = (y1 + y2) / 2
                alpha_start = math.degrees(math.atan(abs_dy / (x_coeff * length)))
                alpha_mid = math.degrees(math.atan(abs_dy / (0.9 * length)))
                alpha_end = math.degrees(math.atan(abs_dy / ((1 - x_coeff) * length)))
                for x, y, areas, alpha, x_loc in zip((x1, xc, x2), (y1, yc, y2), 
                                    (
                                        (additional_start_ta, additional_start_ba),
                                        (additional_mid_ta, additional_mid_ba),
                                        (additional_end_ta, additional_end_ba),
                                        ),
                                        (alpha_start, alpha_mid, alpha_end),
                                        ('S', 'M', 'E')
                                        ):
                    for area, loc, sign in zip(areas, ('T', 'B'), (1, -1)):
                        area *= 10000
                        if area > 0.5 or area < -.5:
                            color = 'blue'
                            if area < 0:
                                color = 'red'
                            r = abs_dy / math.sin(alpha)
                            dx = r * math.cos(rotation + sign * alpha)
                            dy = r * math.sin(rotation + sign * alpha)
                            # Add text item in pyqtgraph
                            text = pg.TextItem(f"{loc}{x_loc}:{area:.2f}", color=color)
                            # text.setFont(QtWidgets.QFont('Arial', font_size))
                            plot.addItem(text)
                            text.setPos(x+dx, y+dy)
    
        # frame_props = etabs.frame_obj.get_section_type_and_geometry(columns)
        # for name in columns:
        #     x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
        #     rotation = etabs.SapModel.FrameObj.GetLocalAxes(name)[0]
        #     props = frame_props.get(name)
        #     b = props.get('b', .5)
        #     d = props.get('d', .5)
        #     polygon = convert_5point_to_8point(x1, y1, b, d, a_=rotation - 90)
        #     for p1, p2 in zip(polygon, polygon[1:] + [polygon[0]]):
        #         block.add_line((p1[0] + dx, p1[1]), (p2[0] + dx, p2[1]), dxfattribs = {'color': 3})
    plot.setMouseEnabled(x=True, y=True)  # Ensure both axes can be zoomed
    
    win.show()
    
    # if filename:
    #     # Export to image file
    #     exporter = pg.exporters.ImageExporter(plot)
    #     exporter.export(filename)
    
    # Start the Qt event loop
    QtWidgets.QApplication.instance().exec_()

def plot_beam_rebars(
    etabs,
    frame_names=None,
    top_rebars='3~16',
    bot_rebars='3~16',
    torsion_rebar='1~20',
    save_path=None
):
    etabs.set_current_unit('kgf', 'm')
    beam_columns = etabs.frame_obj.get_beams_columns_on_stories()
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = {'beam': 'black', 'top': 'blue', 'bot': 'red', 'text': 'green'}
    abs_dy = .2
    x_coeff = 0.1

    top_rebars_areas = sum(int(n) * math.pi * (int(d)/1000)**2 / 4 for n, d in (t.split('~') for t in top_rebars.split('+')))
    bot_rebars_areas = sum(int(n) * math.pi * (int(d)/1000)**2 / 4 for n, d in (t.split('~') for t in bot_rebars.split('+')))
    torsion_rebars_areas = sum(int(n) * math.pi * (int(d)/1000)**2 / 4 for n, d in (t.split('~') for t in torsion_rebar.split('+')))

    for story, level in etabs.story.storyname_and_levels().items():
        ret = beam_columns.get(story, None)
        if ret is None:
            continue
        beams, columns = ret
        if frame_names is not None:
            beams = set(beams).intersection(frame_names)
        if len(beams) == 0:
            continue
        for name in beams:
            x1, y1, x2, y2 = etabs.frame_obj.get_xy_of_frame_points(name)
            ax.plot([x1, x2], [y1, y2], color=colors['beam'], linewidth=2)
            ret = etabs.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
            n = ret[0]
            if n % 2:
                i = j = int(n / 2) + 1
            else:
                i = int(n / 2)
                j = i + 1
            # start rebars
            start_ta = ret[4][0]
            start_ba = ret[6][0]
            start_lt = ret[10][0] / 2
            additional_start_ta = start_ta * 0.9 - top_rebars_areas + start_lt - torsion_rebars_areas
            additional_start_ba = start_ba - bot_rebars_areas + start_lt - torsion_rebars_areas
            # end rebars
            end_ta = ret[4][-1]
            end_ba = ret[6][-1]
            end_lt = ret[10][-1] / 2
            additional_end_ta = end_ta * 0.9 - top_rebars_areas + end_lt - torsion_rebars_areas
            additional_end_ba = end_ba - bot_rebars_areas + end_lt - torsion_rebars_areas
            # middle rebars
            mid_ta = (ret[4][i] + ret[4][j]) / 2
            mid_ba = (ret[6][i] + ret[6][j]) / 2
            mid_lt = (ret[10][i] + ret[10][j]) / 2 / 2
            additional_mid_ta = mid_ta - top_rebars_areas + mid_lt - torsion_rebars_areas
            additional_mid_ba = mid_ba * 1.1 - bot_rebars_areas + mid_lt - torsion_rebars_areas
            xc = (x1 + x2) / 2
            yc = (y1 + y2) / 2
            length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if (x2 - x1) == 0:
                rotation = math.pi / 2
            else:
                rotation = math.atan((y2 - y1) / (x2 - x1))
            alpha_start = math.atan(abs_dy / (x_coeff * length))
            alpha_mid = math.atan(abs_dy / (0.9 * length))
            alpha_end = math.atan(abs_dy / ((1 - x_coeff) * length))
            for (x, y, areas, alpha) in zip(
                (x1, xc, x2), (y1, yc, y2),
                (
                    (additional_start_ta, additional_start_ba),
                    (additional_mid_ta, additional_mid_ba),
                    (additional_end_ta, additional_end_ba),
                ),
                (alpha_start, alpha_mid, alpha_end),
            ):
                for area, loc, sign, color in zip(
                    areas, ('top', 'bot'), (1, -1), (colors['top'], colors['bot'])
                ):
                    area_val = area * 10000
                    if abs(area_val) > 0.5:
                        # Use a fraction of beam length for offset
                        offset = 0.05 * length
                        angle = math.atan2(y2 - y1, x2 - x1)
                        # Position text above/below beam
                        tx = x + offset * math.cos(angle + sign * math.pi/2)
                        ty = y + offset * math.sin(angle + sign * math.pi/2)
                        ax.text(tx, ty, f"{loc}={area_val:.2f}", color=color, fontsize=8, rotation=math.degrees(angle), va='center', ha='center')
    ax.set_aspect('equal')
    ax.set_title("Beam Rebars Layout")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300)
    else:
        plt.show()



