import math
import string
import random
from pathlib import Path
from typing import List

import numpy as np

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



