from pathlib import Path

import FreeCAD
import FreeCADGui

from PySide2.QtWidgets import QMessageBox
from PySide2 import QtCore


class CheckWorker(QtCore.QThread):

    updateAvailable = QtCore.Signal(list)

    def __init__(self, software='civilTools'):
        QtCore.QThread.__init__(self)
        self.software = software

    def run(self):
        try:
            import git
        except ImportError:
            print('git did not installed')
            return
        FreeCAD.Console.PrintLog(f"Checking for available updates of the {self.software} workbench\n")
        software_dir = Path(FreeCAD.getUserAppDataDir()) / "Mod" / f"{self.software}"
        etabs_api_dir = Path(FreeCAD.getUserAppDataDir()) / "Mod" / "etabs_api"
        updates = []
        for directory in (software_dir, etabs_api_dir):
            print(directory)
            if directory.exists() and (directory / '.git').exists():
                gitrepo = git.Git(str(directory))
                try:
                    gitrepo.fetch()
                    if "git pull" in gitrepo.status():
                        updates.append(directory.name)
                except:
                    # can fail for any number of reasons, ex. not being online
                    pass
        
        print(updates)
        self.updateAvailable.emit(updates)

def check_updates(software='civilTools'):
    FreeCAD.software_update_checker = CheckWorker(software)
    FreeCAD.software_update_checker.updateAvailable.connect(show_message)
    FreeCAD.software_update_checker.start()

def show_message(avail):
    if avail:
        FreeCAD.Console.PrintLog("An update is available\n")
        software = '<span style=" font-size:9pt; font-weight:600; color:#0000ff;">%s</span>'
        message = '<html>Update available for %s' % software  % avail[0]
        if len(avail) == 2:
            message += ' and %s' % software % avail[1]
        message += ', Do you want to update?</html>'
        if QMessageBox.question(
            None,
            'Updata Available',
            message,
            ) == QMessageBox.Yes:
            FreeCADGui.runCommand("Std_AddonMgr")
    else:
        FreeCAD.Console.PrintLog("No update available\n")
    if hasattr(FreeCAD,"software_update_checker"):
        del FreeCAD.software_update_checker