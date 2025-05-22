
import os
import sys
import winreg
import subprocess
import platform
# com
import winerror
import pythoncom
from win32com.shell import shell, shellcon
from win32com.server.exception import COMException
# win32
import win32gui_struct
import win32gui
import win32con
import win32process
import win32api
# XML
import xml.etree.ElementTree as et
# Process
import subprocess
# log
import logging

import time
import pychee6

# global const
CWD = os.path.split(__file__)[0]

class SHEContext:
    def __init__(self):
        self.selection = []
        self.isBackground = False
        self.type = set()
        self.flag = 0
        self.defaultOnly = False

    def addSelection(self, selection):
        self.selection.append(selection)
        if os.path.isdir(selection):
            self.type.add("dir")
        elif os.path.isfile(selection):
            self.type.add("file")

    def setFlag(self, uFlags):
        self.flag = uFlags
        if (uFlags & 0x000F) == shellcon.CMF_NORMAL:  # use == here, since CMF_NORMAL=0
            print("[==] SHEContext::flag CMF_NORMAL")
        elif uFlags & shellcon.CMF_VERBSONLY:  # Short cut item
            print("[==] SHEContext::flag CMF_VERBSONLY")
        elif uFlags & shellcon.CMF_EXPLORE:  # in explorer
            print("[==] SHEContext::flag CMF_EXPLORE")
        elif uFlags & shellcon.CMF_DEFAULTONLY:  # should do nothing
            print("[==] SHEContext::flag CMF_DEFAULTONLY")
            self.defaultOnly = True
        else:  # something wrong maybe
            print("[==] SHEContext::flag ** unknown flags ", uFlags)

class ShellExtension:
    _register_tag_ = "LycheeCli"
    _reg_progid_ = "Python.LycheeCli.x1nt"
    _reg_desc_ = "LycheeCli from x1nt"
    _reg_clsid_ = "{7C15377B-26A0-4588-A594-12F95CABD4A1}"
    _com_interfaces_ = [
        shell.IID_IShellExtInit,
        shell.IID_IContextMenu
    ]
    _public_methods_ = shellcon.IContextMenu_Methods + shellcon.IShellExtInit_Methods

    def Initialize(self, folder, dataobj, hkey):
        self.context = SHEContext()
        self.cli = pychee6.LycheeClient(base_url = os.getenv("LYCHEE_HOST"), verbose=False)
        if os.getenv("LYCHEE_TOKEN"):
            self.cli.login_by_token(os.getenv("LYCHEE_TOKEN"))
        else:
            self.cli.login_by_user(os.getenv("LYCHEE_USERNAME"), os.getenv("LYCHEE_PASSWORD"))

        if dataobj:  # select file/directory
            try:
                format_etc = win32con.CF_HDROP, None, pythoncom.DVASPECT_CONTENT, -1, pythoncom.TYMED_HGLOBAL
                sm = dataobj.GetData(format_etc)
            except pythoncom.com_error:
                raise COMException(desc='GetData Error', scode=winerror.E_INVALIDARG)
            selection = [shell.DragQueryFile(sm.data_handle, x) for x in range(shell.DragQueryFile(sm.data_handle, -1))]
            for s in selection:
                self.context.addSelection(s)

        if folder:  # select directory background
            targetDir = shell.SHGetPathFromIDList(folder)
            self.context.addSelection(targetDir)
            self.context.isBackground = True

        # for f in self.context.selection:
        #     print(f"[==] ShellExtension::Initialize select file : {f.encode("gbk")}" )

    def QueryContextMenu(self, hMenu, indexMenu, idCmdFirst, idCmdLast, uFlags):
        print ("[===] QueryContextMenu", hMenu, indexMenu, idCmdFirst, idCmdLast, uFlags)
        self.context.setFlag(uFlags)
        self.index_albumid = {}
        
        self.menu_tree = self.cli.get_album_tree()
        idCmd = idCmdFirst

        # if self.context.isBackground:

        if len(self.menu_tree) == 0:
            return 0

        # add popup menu
        root_menu = win32gui.CreatePopupMenu()
        win32gui.InsertMenu(
            hMenu,
            indexMenu,
            win32con.MF_STRING | win32con.MF_BYPOSITION | win32con.MF_POPUP,
            root_menu,
            "LycheeCli")
        
        win32gui.InsertMenu(
            root_menu,
            -1,
            win32con.MF_STRING | win32con.MF_BYPOSITION,
            idCmd,
            f"{["上传","下载"][self.context.isBackground]}到此处 {idCmd}")
        self.index_albumid[idCmd - idCmdFirst] = ("/","all_album")
        idCmd += 1

        win32gui.InsertMenu(
            root_menu,
            -1,
            win32con.MF_SEPARATOR | win32con.MF_BYPOSITION,
            0,
            None)

        from collections import deque
        queue = deque(self.menu_tree)
        while queue:
            node = queue.popleft()
            tmp_menu = win32gui.CreatePopupMenu()
            win32gui.InsertMenu(
                node.get("parent_menu", root_menu),
                -1,
                win32con.MF_STRING | win32con.MF_BYPOSITION | win32con.MF_POPUP,
                tmp_menu,
                node['original'])

            win32gui.InsertMenu(
                tmp_menu,
                -1,
                win32con.MF_STRING | win32con.MF_BYPOSITION,
                idCmd,
                f"{["上传","下载"][self.context.isBackground]}到此处 {idCmd}")
            self.index_albumid[idCmd - idCmdFirst] = (node['id'],node['original'])
            idCmd += 1

            if idCmd >= idCmdLast:   # 如果超出限制 则可能出现未定义行为
                break

            win32gui.InsertMenu(
                tmp_menu,
                -1,
                win32con.MF_SEPARATOR | win32con.MF_BYPOSITION,
                0,
                None)
            
            for child in node['children']:
                queue.append(child)
                child['parent_menu'] = tmp_menu

        return idCmd - idCmdFirst  # Must return number of menu items we added.

    def InvokeCommand(self, ci):
        mask, hwnd, verb, params, dir, nShow, hotkey, hicon = ci
        print("[==]", mask, hwnd, verb, params, dir, nShow, hotkey, hicon)

        if not isinstance(verb, int):
            print("[!!] InvokeCommand: not a valid index [%s]" % str(verb))
            return

        album_id,title = self.index_albumid[verb]
        print("[==] selected menu item:", album_id)

        if self.context.isBackground: # download
            path = os.path.join(dir,title)
            os.makedirs(path, exist_ok=True)
            commandLine = f'start cmd.exe /k python.exe -m pychee6.cli d_a {album_id} "{path}"'
            res = subprocess.Popen(commandLine, shell=True, cwd=dir)
            print("[==] InvokeCommand: ", commandLine, "res: ", res)
        else: # upload
            for s in self.context.selection:
                if os.path.isdir(s):
                    commandLine = f'start cmd.exe /k python.exe -m pychee6.cli u_a {album_id} "{s}"'
                elif os.path.isfile(s):
                    commandLine = f'start cmd.exe /k python.exe -m pychee6.cli u_p {album_id} "{s}"'
                res = subprocess.Popen(commandLine, shell=True, cwd=dir)
                print("[==] InvokeCommand: ", commandLine, "res: ", res)

    def GetCommandString(self, cmd, typ):
        return "LycheeCli"


REGISTER_PATH_LIST = [
    "*\\shellex\\ContextMenuHandlers\\",
    "directory\\shellex\\ContextMenuHandlers\\",
    "directory\\background\\shellex\\ContextMenuHandlers\\"
]

def addRegisterKeyUnderPath(aPath):
    key = winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        aPath + ShellExtension._register_tag_
    )
    winreg.SetValueEx(key, None, 0, winreg.REG_SZ, ShellExtension._reg_clsid_)

def removeRegisterKeyUnderPath(aPath):
    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, aPath + ShellExtension._register_tag_)

def DllRegisterServer():
    for path in REGISTER_PATH_LIST:
        addRegisterKeyUnderPath(path)
    print(ShellExtension._reg_desc_, "registration [ContextMenuHandler] complete.")

    # Add to approve list
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "Software\\Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Approved", 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(key, ShellExtension._reg_clsid_, 0, winreg.REG_SZ, ShellExtension._reg_progid_)
    print(ShellExtension._reg_desc_, "Add to approve list")

def DllUnregisterServer():
    try:
        for path in REGISTER_PATH_LIST:
            removeRegisterKeyUnderPath(path)
    except OSError as details:
        import errno
        if details.errno != errno.ENOENT:
            raise
    print(ShellExtension._reg_desc_, "unregistration [ContextMenuHandler] complete.")

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "Software\\Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Approved", 0, winreg.KEY_ALL_ACCESS)
        winreg.DeleteValue(key, ShellExtension._reg_clsid_)
    except OSError as details:
        import errno
        if details.errno != errno.ENOENT:
            raise
    print(ShellExtension._reg_desc_, "Remove Approve list complete.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: [--register|--unregister]")
        sys.exit(1)

    # 必须指定 LYCHEE_HOST , 并且 LYCHEE_TOKEN 或 LYCHEE_USERNAME 和 LYCHEE_PASSWORD 指定其一
    if not os.getenv("LYCHEE_HOST") or (not os.getenv("LYCHEE_TOKEN") and not os.getenv("LYCHEE_USERNAME")):
        print("Please set LYCHEE_HOST environment variable, and LYCHEE_TOKEN or LYCHEE_USERNAME and LYCHEE_PASSWORD")
        sys.exit(1)

    if platform.system() != "Windows":
        print("This script only works on Windows")
        sys.exit(1)
        
    from win32com.server import register
    register.UseCommandLine(ShellExtension,
                             finalize_register=DllRegisterServer,
                             finalize_unregister=DllUnregisterServer)