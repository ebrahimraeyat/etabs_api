from pathlib import Path
import os
import subprocess
import time
import tempfile
from dataclasses import dataclass

import comtypes.client

import freecad_funcs

import clear_comtypes_cache


# Constants for software executable names
ETABS_EXE = 'etabs.exe'
SAP2000_EXE = 'sap2000.exe'
SAFE_EXE = 'safe.exe'

missing_packages = []
try:
    import psutil
except ImportError:
    missing_packages.append('psutil')
try:
    from pywinauto import Application
except ImportError:
    missing_packages.append('pywinauto')
if missing_packages:
    freecad_funcs.install_packages(missing_packages)
import psutil
from pywinauto import Application

@dataclass
class SoftwareInfo:
    proc: list

    def __init__(self, proc):
        '''
        Initialize the SoftwareInfo object with a process.

        Args:
            proc (psutil.Process): The process to be initialized.
        '''
        self.proc = proc
        self.__pos_init__()

    def __pos_init__(self):
        self.name = self.proc.info['name']
        self.exe_path = Path(self.proc.info['exe'])
        self.pid = self.proc.info['pid']
        self.software_name = self.get_software_name()
        self.register_exe = self.get_registered_path()
        self.screenshot_path = self.get_screenshot_path()

    def get_screenshot_path(self):
        '''
        Get the screenshot path for the software.
        '''
        temp_dir = Path(tempfile.gettempdir())
        screenshot_path = temp_dir / f"{self.software_name}_{self.pid}.png"
        return screenshot_path

    def get_software_name(self):
        '''
        Get the software name from the executable path.
        '''
        exe_name = self.exe_path.name.lower()
        if exe_name == ETABS_EXE:
            return "ETABS"
        elif exe_name == SAP2000_EXE:
            return "SAP2000"
        elif exe_name == SAFE_EXE:
            return "SAFE"
        else:
            return 'Unknown'
        
    def get_registered_path(self):
        register_exe = self.exe_path.parent / f"Register{self.software_name.upper()}.exe"
        return register_exe
    
    @property
    def app(self):
        '''
        Get the application object using pywinauto.
        '''
        try:
            app = Application().connect(process=self.pid)
            return app
        except Exception as e:
            print(f"Error connecting to application: {e}")
            return None

    def terminate(self, save: bool = True):
        '''
        Terminate the process.
        '''
        try:
            if save:
                self.save_software_with_pywinauto() # Save the software before terminating
            print(f"Terminating process {self.name} with PID {self.pid}")
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except psutil.TimeoutExpired:
            print(f"Process {self.name} did not terminate in time.")
        except psutil.NoSuchProcess:
            print(f"Process {self.name} no longer exists.")
        except psutil.AccessDenied:
            print(f"Access denied to process {self.name}.")

    def exists(self):
        '''
        Check if the executable path exists.
        '''
        return self.exe_path.exists()
        
    def __str__(self):
        return f"{self.name} - {self.exe_path} - {self.pid}"
    
    def __repr__(self):
        return f"{self.name} - {self.exe_path} - {self.pid}"
    
    def __eq__(self, other):
        if isinstance(other, SoftwareInfo):
            return self.exe_path == other.exe_path
        return False
    
    def register(self,
                 close: bool = True,
                 save: bool = True,
                 open: bool = False,
                 ) -> bool:
        if not self.register_exe.exists():
            raise FileNotFoundError(f"Register not found at {self.register_exe}")

        try:
            # Run RegisterETABS.exe with admin privileges
            print(f"Registering {self.software_name} using {self.register_exe}...")
            if close:
                self.terminate(save=save)
            ret = subprocess.run(
                [str(self.register_exe)],
                check=True,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if 'error' in ret.stdout.decode():
                print(f"Failed to register ETABS: {ret.stdout.decode()}")
                return False
            print("ETABS successfully registered.")
            if open:
                self.open()
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to register ETABS: {e}")
            return False
        
    def open_explorer_to_register_exe(self):
        """
        Open Windows Explorer in the folder containing the register executable.
        """
        if not self.register_exe.exists():
            raise FileNotFoundError(f"Register executable not found at {self.register_exe}")

        # Open Windows Explorer in the folder containing the register executable
        subprocess.Popen(f'explorer /select,"{self.register_exe}"')

    def save_software_with_pywinauto(self):
        """
        Save the software using pywinauto by simulating Ctrl + S.
        If a save dialog appears, handle it by either waiting for the user to save
        or automatically entering a random file name and saving the file.

        Args:
            exe_path (str): Path to the software executable.
        """
        window = self.set_focus()
        # Simulate Ctrl + S to save the file
        window.type_keys("^s", with_spaces=True)
        time.sleep(2)  # Wait for the save dialog to appear (if any)
        print("File saved successfully.")

    def open(self):
        """
        Open the software using subprocess.
        """
        print(f"Opening {self.name} in {self.exe_path}...")
        subprocess.run(
            [str(self.exe_path)],
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def set_focus(self, timeout=0.5):
        """
        Set focus to the software window using pywinauto.
        """
        window = self.get_window()
        if window is not None:
            window.set_focus()
            time.sleep(timeout)
        return window
    
    def get_window(self):
        """
        Get the top window of the software using pywinauto.
        """
        app = self.app
        window = app.top_window()
        if window:
            return window
        return None
    
    def get_screen_shot(self):
        window = self.set_focus()
        if window is not None:
            # Create a temporary directory to save screenshots
            screenshot = window.capture_as_image()  # PIL Image
            screenshot.save(self.screenshot_path, format="PNG")  # Save the screenshot to TEMP
            print(f"Screenshot saved to {self.screenshot_path}")
            return window
        return None
    
    def get_tlb_path(self, tlb_file: str= 'CSiAPIv1.tlb'):
        '''
        Get the TLB path for the software.
        '''
        tlb_path = self.exe_path.parent / tlb_file
        if not tlb_path.exists():
            tlb_path = self.exe_path.parent / "NativeAPI" / "x64" / tlb_file
        if tlb_path.exists():
            return tlb_path
        else:
            print(f"{tlb_file} file not found for {self.software_name} at {tlb_path}.")
            return None
    
def get_softwares_process(
        exe_names: list=['etabs.exe', 'sap2000.exe', 'safe.exe'],
        ) -> list:
        '''
        Retrieves the executable paths of specified software by scanning running processes.

        Args:
            exe_names (list): A list of executable names to search for. Defaults to 
                                ['etabs.exe', 'sap2000.exe', 'safe.exe']. If a single string 
                                is provided, it will be converted into a list.

        Returns:
            list: A list of `SoftwareInfo` objects containing information about the 
                    processes whose executable names match the provided list.

        Notes:
            - The function uses `psutil` to iterate over running processes and match 
                their executable names with the provided list.
            - Executable names are case-insensitive and automatically appended with 
                ".exe" if not already present.
            - Processes that cannot be accessed due to permissions or no longer exist 
                are skipped.
        '''
        
        if isinstance(exe_names, str):
            exe_names = [exe_names]
        exe_names = [name.lower() for name in exe_names]
        exe_names = [f"{name}.exe" if not name.endswith('.exe') else name for name in exe_names]
        softwares = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                exe = proc.info['name']
                if exe.lower() in exe_names:
                    softwares.append(SoftwareInfo(proc))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return softwares

def connect_to_software(software: SoftwareInfo):
    """Connect to the selected software and save the path."""
    # Clear comtypes gen folder before connecting
    try:
        software.register()
        gen_dir = clear_comtypes_gen_folder()
        return True
    except Exception as e:
        print(f"Failed to register {software.software_name}: {e}")
        return None
    # tlb_path = software.get_tlb_path()
    # if tlb_path is None:
    #     return None
    # try:
    #     gen_wrappers(tlb_path, gen_dir)
    #     print(f"{tlb_path=}")
    #     return True
    # except Exception as e:
    #     print(f"Failed to generate wrappers for {software.software_name}: {e}")
    #     return None

def gen_wrappers(tlb_path, gen_dir):
    os.makedirs(gen_dir, exist_ok=True)
    comtypes.client.gen_dir = str(gen_dir)
    comtypes.client.GetModule(str(tlb_path))  # generates module matching that TLB

def get_software_name(software):
    '''
    Get the software name from the executable path.
    '''
    exe_path = Path(software.exe_path)
    if exe_path.name.lower() == 'etabs.exe':
        return "ETABS"
    elif exe_path.name.lower() == 'sap2000.exe':
        return "SAP2000"
    elif exe_path.name.lower() == 'safe.exe':
        return "SAFE"
    else:
        return None
    
def get_gen_dir():
    """
    Get the comtypes gen folder path.
    """
    import comtypes.client
    gen_dir = comtypes.client._code_cache._find_gen_dir()
    # roaming_dir =os.getenv('APPDATA')
    # gen_dir = Path(roaming_dir) / 'comtypes' / 'gen'
    if gen_dir:
        gen_dir = Path(gen_dir)
    return gen_dir

def clear_comtypes_gen_folder():
    """
    Clears the comtypes gen folder.
    """
    gen_dir = get_gen_dir()
    clear_comtypes_cache.clear_cache()
    # os.makedirs(gen_dir, exist_ok=True)
    return gen_dir

def register_software(software: SoftwareInfo,
                      open: bool = True,
                      ):
    '''
    Register ETABS, SAP2000, or SAFE.
    '''
    from PySide2.QtWidgets import QMessageBox
    try:
        # Run RegisterETABS.exe with admin privileges
        ret = software.register()
        if ret:
            print("ETABS successfully registered.")
            QMessageBox.information(
                None,
                "Registration Successful",
                f"{software.software_name} has been successfully registered.",
            )
            if open:
                software.open()
        else:
            software.open_explorer_to_register_exe()
    except subprocess.CalledProcessError as e:
        print(f"Failed to register ETABS: {e}")
        QMessageBox.critical(
            None,
            "Registration Failed",
            f"Failed to register {software.software_name}. Please Run the {software.register_exe} with Administrator.",
        )
        software.open_explorer_to_register_exe()

