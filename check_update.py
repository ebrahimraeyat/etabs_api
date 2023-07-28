from pathlib import Path

from PySide2 import QtWidgets
from PySide2 import QtCore

import FreeCAD
import FreeCADGui


class GitFailed(RuntimeError):
    """The call to git returned an error of some kind"""


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
            # updates.append(directory)
            if directory.exists() and (directory / '.git').exists():
                gitrepo = git.Git(str(directory))
                try:
                    gitrepo.fetch()
                    status = gitrepo.status()
                    if "git add" in status:
                        restart_freecad()
                    elif "git pull" in status:
                        updates.append(directory)
                except:
                    # can fail for any number of reasons, ex. not being online
                    pass
        
        self.updateAvailable.emit(updates)

def check_updates(software='civilTools'):
    FreeCAD.software_update_checker = CheckWorker(software)
    FreeCAD.software_update_checker.updateAvailable.connect(show_message)
    FreeCAD.software_update_checker.start()

def show_message(avail):
    if avail:
        FreeCAD.Console.PrintLog("An update is available\n")
        software = '<span style=" font-size:9pt; font-weight:600; color:#0000ff;">%s</span>'
        message = '<html>Update available for %s' % software  % avail[0].name
        if len(avail) == 2:
            message += ' and %s' % software % avail[1].name
        message += ', Do you want to update?</html>'
        if QtWidgets.QMessageBox.question(
            None,
            'Updata Available',
            message,
            ) == QtWidgets.QMessageBox.Yes:
            update(avail)
    else:
        FreeCAD.Console.PrintLog("No update available\n")
    if hasattr(FreeCAD,"software_update_checker"):
        del FreeCAD.software_update_checker

def update(repos_path: list):
    import subprocess, os, shutil
    git_exe = shutil.which("git")
    if not git_exe:
        link = 'https://github.com/git-for-windows/git/releases/download/v2.37.2.windows.2/Git-2.37.2.2-64-bit.exe'
        link = "<a href='{link}'>here</a>"
        text = '<span style=" font-size:9pt; font-weight:600; color:#0000ff;">%s</span>'
        message = '<html>Git not installed on your system, Please download and install it from %s' % text  % link
        QtWidgets.QMessageBox.warning(None, 'Install Git', message)
        return
    final_args = ['git.exe', 'pull']
    old_dir = os.getcwd()
    failed = False
    for repo_path in repos_path:
        os.chdir(str(repo_path))
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
                "Basic git update failed with the following message:" \
                + str(e) \
                + "\n"
            )
            failed = True
    os.chdir(old_dir)
    if not failed:
        msg = '''Update have been done Successfully,
        Restart FreeCAD to take changes effect.'''
        QtWidgets.QMessageBox.information(None, "Successful", msg)
        restart_freecad()
    else:
        msg = 'Update failed.'
        QtWidgets.QMessageBox.warning(None, "Failed", msg)

def restart_freecad():
    # return
    """Shuts down and restarts FreeCAD"""
    args = QtWidgets.QApplication.arguments()[1:]
    # FreeCADGui.getMainWindow().deleteLater()
    if FreeCADGui.getMainWindow().close():
        QtCore.QProcess.startDetached(
            QtWidgets.QApplication.applicationFilePath(), args
        )
            
