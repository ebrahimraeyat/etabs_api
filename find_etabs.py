from pathlib import Path

from PySide.QtGui import QMessageBox

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui as Gui

import importlib
import etabs_obj
importlib.reload(etabs_obj)


def open_browse(
        ext: str = '.EDB',
        ):
    from PySide.QtGui import QFileDialog
    filters = f"{ext[1:]} (*{ext})"
    filename, _ = QFileDialog.getOpenFileName(None, 'select file',
                                            None, filters)
    if not filename:
        return None
    if not filename.upper().endswith(ext):
        filename += ext
    return filename

def find_etabs(
    run=False,
    backup=False,
    filename=None,
    show_warning: bool = True,
    # software: str='ETABS',
    ):
    '''
    try to find etabs in this manner:
    1- connect to open ETABS model
    2- try to open etabs if user set the etabs_exe_path

    run : if True it runs the model
    backup: if True it backup from the main file
    '''
    software_name = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/civilTools").GetInt("software_name", 0)
    software = {
        0: "ETABS",
        1: "SAP2000",
        2: "SAFE",
        }.get(software_name, 'ETABS')

    # try to connect to opening etabs software
    etabs = etabs_obj.EtabsModel(backup=backup, software=software)

    # if not etabs.success:
    #     pass
    if etabs.success:
        filename_path = etabs.get_filename()
        if filename_path and filename_path.exists():
            filename = str(filename_path)
    elif show_warning:
        QMessageBox.warning(
        None,
        software,
        f'Please Open {software} Software. If {software} is now open, try register etabs first.'
        )
    if (
        filename is None and
        etabs.success and
        hasattr(etabs, 'SapModel')
        ):
        filename = open_browse()
    if filename is None and etabs.success and show_warning:
        QMessageBox.warning(None, software, f'Please Open {software} Model and Run this command again.')
    elif (
        hasattr(etabs, 'success') and
        etabs.success and
        filename != etabs.SapModel.GetModelFilename()
        ):
            etabs.SapModel.File.OpenFile(str(filename))
    # run etabs
    if (
        run and
        etabs.success and
        filename is not None and
        hasattr(etabs, 'SapModel') and
        not etabs.SapModel.GetModelIsLocked()
        ):
        QMessageBox.information(
            None,
            f'Run {software} Model',
            'Model did not run and needs to be run. It takes some times.')
        progressbar = FreeCAD.Base.ProgressIndicator()
        progressbar.start(f"Run {software} Model ... ", 2)
        progressbar.next(True)
        etabs.run_analysis()
        progressbar.stop()
    if isinstance(filename, str) and Path(filename).exists():
        filename = Path(filename)
    return etabs, filename

def get_mdiarea():
    """ Return FreeCAD MdiArea. """
    import PySide
    mw = Gui.getMainWindow()
    if not mw:
        return None
    childs = mw.children()
    for c in childs:
        if isinstance(c, PySide.QtGui.QMdiArea):
            return c
    return None

def get3dview():
    from PySide import QtGui
    mw = Gui.getMainWindow()
    childs=mw.findChildren(QtGui.QMainWindow)
    for i in childs:
        if i.metaObject().className() == "Gui::View3DInventor":
            return i
    return None

def show_win(win, in_mdi=True):
    mdi = get_mdiarea()
    if mdi is None:
        Gui.Control.showDialog(win)
    else:
        if in_mdi:
            mdi.addSubWindow(win.form)
        win.form.exec_()

