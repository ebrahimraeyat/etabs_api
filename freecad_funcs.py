from typing import Union
from pathlib import Path

from PySide2.QtWidgets import QMessageBox

import FreeCAD
import FreeCADGui
import Part

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
        from PySide2 import QtCore, QtWidgets
        vm = QtWidgets.QDockWidget()

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

def show_help(
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
    software_help_dir = Path(FreeCAD.getUserAppDataDir()) / "Mod" / f"{software}" / 'help'
    help_path = software_help_dir / filename
    Help.show(str(help_path))

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
    user_path = Path(FreeCAD.getUserAppDataDir() / 'Mod' / 'FreeCAD-Help')
    old_dir = os.getcwd()
    failed = False
    os.chdir(str(user_path.parent))  # Mod folder
    for repo in repos:
        final_args = [git_exe, 'clone', f'{repo}:{user_path}']
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