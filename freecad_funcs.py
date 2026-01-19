import os, sys, subprocess
from typing import Union
from pathlib import Path
try:
    import FreeCAD
    import Part
except ModuleNotFoundError:
    pass

if FreeCAD and FreeCAD.GuiUp:
    import FreeCADGui

try:
    from PySide2.QtWidgets import QMessageBox, QFileDialog
    from PySide2 import QtCore
    from PySide2 import QtWidgets
except ModuleNotFoundError:
    pass


import pandas as pd

def rectangle_face(
    bx: Union[float, int],
    by: Union[float, int],
    center: FreeCAD.Vector = FreeCAD.Vector(0, 0, 0),
    ):

    v1, v2, v3, v4 = rectangle_vertexes(bx, by, center)
    return Part.Face(Part.makePolygon([v1, v2, v3, v4, v1]))

def rectangle_vertexes(
                       bx: Union[float, int],
                       by: Union[float, int],
                       center: FreeCAD.Vector = FreeCAD.Vector(0, 0, 0),
                       ):
    dx = bx / 2
    dy = by / 2
    v1 = center.add(FreeCAD.Vector(-dx, -dy, 0))
    v2 = center.add(FreeCAD.Vector(dx, -dy, 0))
    v3 = center.add(FreeCAD.Vector(dx, dy, 0))
    v4 = center.add(FreeCAD.Vector(-dx, dy, 0))
    return [v1, v2, v3, v4]

def column_shape(
    width: float,
    height: float,
    N: int,
    M: int,
    main_diameter: int,
    tie_diameter: int = 10,
    cover: int = 40,
    center: FreeCAD.Vector = FreeCAD.Vector(0, 0, 0),
):
    rect = rectangle_face(width, height, center)
    c = cover + tie_diameter + main_diameter / 2
    b = width - 2 * (cover + tie_diameter) - main_diameter
    dx = b / (N - 1)
    h = height - 2 * (cover + tie_diameter) - main_diameter
    dy = h / (M - 1)
    x1 = -width / 2 + c
    y1 = -height / 2 + c
    x2 = width / 2 - c
    y2 = height / 2 - c
    circles = []
    radius = main_diameter / 2
    for i in range(N):
        for j in range(M):
            x = -width / 2 + (c + i * dx)
            y = -height / 2 + (c + j * dy)
            if x1 < x < x2 and y1 < y < y2:
                continue
            center = FreeCAD.Vector(x, y, 0)
            circle = Part.makeCircle(radius, center)
            circles.append(circle)
    return Part.makeCompound([rect] + circles)

def findWidget(
        name: str,
        mw=None,
        ):

    "finds the manager widget, if present"

    import FreeCADGui
    from PySide import QtGui
    if mw is None:
        mw = FreeCADGui.getMainWindow()
    vm = mw.findChild(QtGui.QDockWidget, name)
    if vm:
        return vm
    return None

def add_dock_widget(
        widget,
        name: str,
        title: str,
        ):
    mw = FreeCADGui.getMainWindow()
    vm = findWidget(name, mw)
    if vm:
        if not vm.isVisible():
            vm.show()
    else:
        from PySide import QtCore, QtGui
        vm = QtGui.QDockWidget()

        # create the dialog
        # dialog = FreeCADGui.PySideUic.loadUi(ui)
        vm.setWidget(widget)
        # widget.form.show()
        vm.setObjectName(name)
        vm.setWindowTitle("civilTools")
        mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, vm)

def show_status_message(
    text: str,
    time: int = 5000,
    ):
    mw = FreeCADGui.getMainWindow()
    sb = mw.statusBar()
    sb.showMessage(text, time)

def ask_to_unlock(etabs):
    if etabs.SapModel.GetModelIsLocked():
        if QMessageBox.question(
            None,
            'Unlock',
            'Model is lock, do you want to unlock the model?',
            ) == QMessageBox.No:
            return 'NO'
        else:
            etabs.unlock_model()


class GitFailed(RuntimeError):
    """The call to git returned an error of some kind"""

def show_help_freecad(
        filename: str,
        software: str = 'civilTools',
        ):
    try:
        import Help
    except ModuleNotFoundError:
        if (QMessageBox.question(
                None,
                "Install Help",
                "You must install Help WB to view the manual, do you want to install it?",
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.No):
            return
        try:
            clone_repos(["https://github.com/FreeCAD/FreeCAD-Help.git"])
            return
        except:
            FreeCADGui.runCommand('Std_AddonMgr',0)
            return
    prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Help")
    if not prefs.GetBool("optionBrowser", True):
        prefs.SetBool("optionBrowser", True)
    software_help_dir = Path(FreeCAD.getUserAppDataDir()) / "Mod" / f"{software}" / 'help'
    help_path = software_help_dir / filename
    Help.show(str(help_path))

def show_help(
        filename: str,
        software: str = 'civilTools',
        ):
    software_help_dir = Path(FreeCAD.getUserAppDataDir()) / "Mod" / f"{software}" / 'help'
    help_path = software_help_dir / filename
    import webbrowser
    webbrowser.open_new(help_path)

def get_git_exe():
    import shutil
    git_exe = shutil.which("git")
    if not git_exe:
        link = 'https://github.com/git-for-windows/git/releases/download/v2.37.2.windows.2/Git-2.37.2.2-64-bit.exe'
        link = "<a href='{link}'>here</a>"
        text = '<span style=" font-size:9pt; font-weight:600; color:#0000ff;">%s</span>'
        message = '<html>Git not installed on your system, Please download and install it from %s' % text  % link
        QMessageBox.warning(None, 'Install Git', message)
        return None
    return git_exe

def clone_repos(repos: list):
    import subprocess, os
    git_exe = get_git_exe()
    if git_exe is None:
        return
    user_path = Path(FreeCAD.getUserAppDataDir()) / 'Mod' / 'FreeCAD-Help'
    old_dir = os.getcwd()
    failed = False
    os.chdir(str(user_path.parent))  # Mod folder
    for repo in repos:
        final_args = [git_exe, 'clone', f'{repo}', f'{user_path}']
        try:
            subprocess.run(
                final_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                shell=True # On Windows this will prevent all the pop-up consoles        
            )
        except GitFailed as e:
            FreeCAD.Console.PrintWarning(
                "Basic git clone failed with the following message:" \
                + str(e) \
                + "\n"
            )
            failed = True
    os.chdir(old_dir)
    if not failed:
        msg = 'Help installed Successfully.'
        QMessageBox.information(None, "Successful", msg)
    else:
        msg = 'Install failed.'
        QMessageBox.warning(None, "Failed", msg)


def import_etabs_mesh_results(
    m,
    result_name_prefix="",
    result_analysis_type=""
):
    from FreeCAD import Console
    import ObjectsFem
    from feminout import importToolsFem
    from femresult import resulttools
    from femtools import femutils

    doc = FreeCAD.newDocument()

    result_mesh_object = None
    res_obj = None

    if len(m["Nodes"]) > 0:
        mesh = importToolsFem.make_femmesh(m)
        res_mesh_is_compacted = False
        nodenumbers_for_compacted_mesh = []

        number_of_increments = len(m["Results"])
        Console.PrintLog(
            "Increments: " + str(number_of_increments) + "\n"
        )
        if len(m["Results"]) > 0:
            for result_set in m["Results"]:
                if "number" in result_set:
                    eigenmode_number = result_set["number"]
                else:
                    eigenmode_number = 0
                step_time = result_set["time"]
                step_time = round(step_time, 2)
                if eigenmode_number > 0:
                    results_name = (
                        "{}EigenMode_{}_Results"
                        .format(result_name_prefix, eigenmode_number)
                    )
                elif number_of_increments > 1:
                    if result_analysis_type == "buckling":
                        results_name = (
                            "{}BucklingFactor_{}_Results"
                            .format(result_name_prefix, step_time)
                        )
                    else:
                        results_name = (
                            "{}Time_{}_Results"
                            .format(result_name_prefix, step_time)
                        )
                else:
                    results_name = (
                        "{}Results"
                        .format(result_name_prefix)
                    )

                res_obj = ObjectsFem.makeResultMechanical(doc, results_name)
                # create result mesh
                result_mesh_object = ObjectsFem.makeMeshResult(doc, results_name + "_Mesh")
                result_mesh_object.FemMesh = mesh
                res_obj.Mesh = result_mesh_object
                res_obj = importToolsFem.fill_femresult_mechanical(res_obj, result_set)

                # more result object calculations
                if not res_obj.MassFlowRate:
                    # information 1:
                    # only compact result if not Flow 1D results
                    # compact result object, workaround for bug 2873
                    # https://www.freecad.org/tracker/view.php?id=2873
                    # information 2:
                    # if the result data has multiple result sets there will be multiple result objs
                    # they all will use one mesh obj
                    # on the first res obj fill: the mesh obj will be compacted, thus
                    # it does not need to be compacted on further result sets
                    # but NodeNumbers need to be compacted for every result set (res object fill)
                    # example frd file: https://forum.freecad.org/viewtopic.php?t=32649#p274291
                    if res_mesh_is_compacted is False:
                        # first result set, compact FemMesh and NodeNumbers
                        res_obj = resulttools.compact_result(res_obj)
                        res_mesh_is_compacted = True
                        nodenumbers_for_compacted_mesh = res_obj.NodeNumbers
                    else:
                        # all other result sets, do not compact FemMesh, only set NodeNumbers
                        res_obj.NodeNumbers = nodenumbers_for_compacted_mesh

                # fill DisplacementLengths
                res_obj = resulttools.add_disp_apps(res_obj)
                # fill vonMises
                res_obj = resulttools.add_von_mises(res_obj)
                # fill principal stress
                # if material reinforced object use add additional values to the res_obj
                if res_obj.getParentGroup():
                    has_reinforced_mat = False
                    for obj in res_obj.getParentGroup().Group:
                        if femutils.is_of_type(obj, "Fem::MaterialReinforced"):
                            has_reinforced_mat = True
                            Console.PrintLog(
                                "Reinforced material object detected, "
                                "reinforced principal stresses and standard principal "
                                "stresses will be added.\n"
                            )
                            resulttools.add_principal_stress_reinforced(res_obj)
                            break
                    if has_reinforced_mat is False:
                        Console.PrintLog(
                            "No reinforced material object detected, "
                            "standard principal stresses will be added.\n"
                        )
                        # fill PrincipalMax, PrincipalMed, PrincipalMin, MaxShear
                        res_obj = resulttools.add_principal_stress_std(res_obj)
                else:
                    Console.PrintLog(
                        "No Analysis detected, standard principal stresses will be added.\n"
                    )
                    # if a pure frd file was opened no analysis and thus no parent group
                    # fill PrincipalMax, PrincipalMed, PrincipalMin, MaxShear
                    res_obj = resulttools.add_principal_stress_std(res_obj)
                # fill Stats
                res_obj = resulttools.fill_femresult_stats(res_obj)

                # create a results pipeline if not already existing
                # pipeline_name = "Pipeline_" + results_name
                # pipeline_obj = doc.getObject(pipeline_name)
                # if pipeline_obj is None:
                #     pipeline_obj = ObjectsFem.makePostVtkResult(doc, res_obj, results_name)
                #     pipeline_visibility = True
                # else:
                #     if FreeCAD.GuiUp:
                #         # store pipeline visibility because pipeline_obj.load makes the
                #         # pipeline always visible
                #         pipeline_visibility = pipeline_obj.ViewObject.Visibility
                #     pipeline_obj.load(res_obj)
                # # update the pipeline
                # pipeline_obj.recomputeChildren()
                # pipeline_obj.recompute()
                # if FreeCAD.GuiUp:

                    # pipeline_obj.ViewObject.updateColorBars()
                    # make results mesh invisible, will be made visible
                    # later in task_solver_ccxtools.py
                    # res_obj.Mesh.ViewObject.Visibility = False
                    # restore pipeline visibility
                    # pipeline_obj.ViewObject.Visibility = pipeline_visibility

        else:
            error_message = (
                "Nodes, but no results found in frd file. "
                "It means there only is a mesh but no results in frd file. "
                "Usually this happens for: \n"
                "- analysis type 'NOANALYSIS'\n"
                "- if CalculiX returned no results "
                "(happens on nonpositive jacobian determinant in at least one element)\n"
                "- just no frd results where requestet in input file "
                "(neither 'node file' nor 'el file' in output section')\n"
            )
            Console.PrintWarning(error_message)

        # create a result obj, even if we have no results but a result mesh in frd file
        # see error message above for more information
        if not res_obj:
            if result_name_prefix:
                results_name = "{}_Results".format(result_name_prefix)
            else:
                results_name = "Results"
            res_obj = ObjectsFem.makeResultMechanical(doc, results_name)
            res_obj.Mesh = result_mesh_object
            # TODO, node numbers in result obj could be set

        if FreeCAD.GuiUp:
            doc.recompute()

    else:
        Console.PrintError(
            "Problem on frd file import. No nodes found in frd file.\n"
        )
        # None will be returned
        # or would it be better to raise an exception if there are not even nodes in frd file?
    FreeCADGui.activeDocument().activeView().viewIsometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCAD.ActiveDocument.getObject('Results').ViewObject.doubleClicked()
    return res_obj

def install_package(package_name:str):
    if QMessageBox.question(
        None,
        'Install Package', f'Package {package_name} must be installed, Do you want to install it?',
        ) == QMessageBox.No:
            return
    import subprocess
    subprocess.check_call(['python', "-m", "pip", "install", package_name])

def install_packages(package_names:Union[str, list]):
    if QMessageBox.question(
        None,
        'Install Package', f"Package {','.join(package_names)} must be installed, Do you want to install?",
        ) == QMessageBox.No:
            return
    if isinstance(package_names, str):
        package_names = [package_names]
    import subprocess
    subprocess.check_call(['python', "-m", "pip", "install", ' '.join(package_names)])

def add_to_clipboard(text):
    df=pd.DataFrame([text])
    df.to_clipboard(index=False,header=False)

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

def get_file_name(suffix: list, etabs=None):
    filters = f"{suffix}(*.{suffix})"
    if etabs is not None:
        directory = str(etabs.get_filepath())
    else:
        directory = ''
    filename, _ = QFileDialog.getSaveFileName(None, 'Get Filename',
                                                directory, filters)
    if filename == '':
        return
    if not filename.endswith(f".{suffix}"):
        filename += f".{suffix}"
    return filename

def get_color(param, pref_intity, color=674321151):
    c = param.GetUnsigned(pref_intity, color)
    r = float((c >> 24) & 0xFF)
    g = float((c >> 16) & 0xFF)
    b = float((c >> 8) & 0xFF)
    return (r, g, b)

def equivalent_height_in_meter(wall):
    inlists = wall.InList
    if not inlists:
        return wall.Height.getValueAs('m').Value, 0
    win = None
    for o in inlists:
        if hasattr(o, 'IfcType') and o.IfcType == 'Window':
            win = o
            break
    if win is None:
        return wall.Height.getValueAs('m').Value, 0
    wall_area = wall.Height * wall.Length
    window_area = win.Height * win.Width
    area = (wall_area) -  (window_area)
    percent = window_area / wall_area
    height = (area / wall.Length).getValueAs('m').Value
    return height, percent.Value

def get_relative_dists(wall):
    wall_trace = wall.Base
    if hasattr(wall, 'base'):
        base = wall.base
    else: # wall load created with user
        return 0, 1
    e1 = wall_trace.Shape.Edges[0]
    e2 = base.Shape.Edges[0]
    p1 = e2.firstVertex().Point
    p2 = e1.firstVertex().Point + wall.Placement.Base
    p3 = e1.lastVertex().Point + wall.Placement.Base
    v1 = p2.sub(p1)
    v2 = p3.sub(p1)
    dist1 = round((v1.Length / base.Length).Value, 3)
    dist2 = round((v2.Length / base.Length).Value, 3)
    assert max(dist1, dist2) <= 1
    return dist1, dist2

def restart_freecad(check_test: bool=True):
    if check_test and os.environ.get('TEST_CIVILTOOLS', 'No') in ('Yes', 'yes'):
        return
    args = QtWidgets.QApplication.arguments()[1:]
    # FreeCADGui.getMainWindow().deleteLater()
    if FreeCADGui.getMainWindow().close():
        QtCore.QProcess.startDetached(
            QtWidgets.QApplication.applicationFilePath(), args
        )