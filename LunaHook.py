from ctypes import CDLL, CFUNCTYPE, Structure, c_char, c_int64, c_uint, c_void_p, c_int, c_bool, c_uint32, c_wchar, c_wchar_p, c_uint64, cast , c_uint8,POINTER,c_char_p
from ctypes.wintypes import DWORD, LPCWSTR
import threading

from translator import XAI_API

def threader(func):
    def _wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()

    return _wrapper
class SearchParam(Structure):
    _fields_ = [
        ("pattern", c_char * 30),
        ("address_method", c_int),
        ("search_method", c_int),
        ("length", c_int),
        ("offset", c_int),
        ("searchTime", c_int),
        ("maxRecords", c_int),
        ("codepage", c_int),
        ("padding", c_int64),
        ("minAddress", c_uint64),
        ("maxAddress", c_uint64),
        ("boundaryModule", c_wchar * 120),
        ("exportModule", c_wchar * 120),
        ("text", c_wchar * 30),
        ("jittype", c_int),
    ]
class ThreadParam(Structure):
    _fields_ = [
        ("processId", c_uint),
        ("addr", c_uint64),
        ("ctx", c_uint64),
        ("ctx2", c_uint64),
    ]

    def __hash__(self):
        return hash((self.processId, self.addr, self.ctx, self.ctx2))

    def __eq__(self, __value):
        return self.__hash__() == __value.__hash__()

    def __repr__(self):
        return "(%s,%x,%x,%x)" % (self.processId, self.addr, self.ctx, self.ctx2)
    
findhookcallback_t = CFUNCTYPE(None, c_wchar_p, c_wchar_p)
ProcessEvent = CFUNCTYPE(None, DWORD)
ThreadEvent_maybe_embed = CFUNCTYPE(None, c_wchar_p, c_char_p, ThreadParam, c_bool)
ThreadEvent = CFUNCTYPE(None, c_wchar_p, c_char_p, ThreadParam)
OutputCallback = CFUNCTYPE(c_bool, c_wchar_p, c_char_p, ThreadParam, c_wchar_p)
ConsoleHandler = CFUNCTYPE(None, c_wchar_p)
HookInsertHandler = CFUNCTYPE(None, DWORD, c_uint64, c_wchar_p)
EmbedCallback = CFUNCTYPE(None, c_wchar_p, ThreadParam)
QueryHistoryCallback = CFUNCTYPE(None, c_wchar_p)

        
class LunaHostWrapper:
    def __init__(self, dll_path):
        self.dll = CDLL(dll_path)

        self.xai_api = XAI_API()  
        self.pids = []
        self.keepref = []
        self.init_functions()

    def init_functions(self):

        self.Luna_SyncThread = self.dll.Luna_SyncThread
        self.Luna_SyncThread.argtypes = ThreadParam, c_bool

        self.Luna_InsertPCHooks = self.dll.Luna_InsertPCHooks
        self.Luna_InsertPCHooks.argtypes = (DWORD, c_int)

        self.Luna_Inject = self.dll.Luna_Inject
        self.Luna_Inject.argtypes = DWORD, LPCWSTR  # DWORD, LPCWSTR

        self.Luna_InsertHookCode = self.dll.Luna_InsertHookCode
        self.Luna_InsertHookCode.argtypes = DWORD, LPCWSTR
        self.Luna_InsertHookCode.restype = c_bool

        self.Luna_RemoveHook = self.dll.Luna_RemoveHook
        self.Luna_RemoveHook.argtypes = DWORD, c_uint64

        self.Luna_CreatePipeAndCheck = self.dll.Luna_CreatePipeAndCheck
        self.Luna_CreatePipeAndCheck.argtypes = (DWORD,)
        self.Luna_CreatePipeAndCheck.restype = c_bool

        self.Luna_Detach = self.dll.Luna_Detach
        self.Luna_Detach.argtypes = (DWORD,)
        self.Luna_FindHooks = self.dll.Luna_FindHooks
        self.Luna_FindHooks.argtypes = (
            DWORD,
            SearchParam,
            c_void_p,
        )
        self.Luna_EmbedSettings = self.dll.Luna_EmbedSettings
        self.Luna_EmbedSettings.argtypes = (
            DWORD,c_uint32, c_uint8, c_bool, c_wchar_p, c_uint32, c_bool
        ) 

        self.Luna_checkisusingembed = self.dll.Luna_checkisusingembed
        self.Luna_checkisusingembed.argtypes = (ThreadParam,)
        self.Luna_checkisusingembed.restype = c_bool

        self.Luna_useembed = self.dll.Luna_useembed
        self.Luna_useembed.argtypes = ThreadParam, c_bool

        self.Luna_embedcallback = self.dll.Luna_embedcallback
        self.Luna_embedcallback.argtypes = ThreadParam, LPCWSTR, LPCWSTR

        self.Luna_Start = self.dll.Luna_Start
        self.Luna_Start.argtypes = (
            c_void_p,
            c_void_p,
            c_void_p,
            c_void_p,
            c_void_p,
            c_void_p,
            c_void_p,
        )
        procs = [
            ProcessEvent(self.onprocconnect),
            ProcessEvent(self.removeproc),
            ThreadEvent_maybe_embed(self.onnewhook),
            ThreadEvent(self.onremovehook),
            OutputCallback(self.handle_output),
            HookInsertHandler(self.newhookinsert),
            EmbedCallback(self.getembedtext),
        ]
        self.keepref += procs
        ptrs = [cast(_, c_void_p).value for _ in procs]
        self.Luna_Start(*ptrs)
    def onprocconnect(self, pid):
        self.pids.append(pid)
    def removeproc(self, pid):
        self.pids.remove(pid)
    def onnewhook(self, hc, hn, tp, isembedable):
        key = (hc, hn.decode("utf8"), tp)
        return True
    def onremovehook(self, hc, hn, tp):
        key = (hc, hn.decode("utf8"), tp)
    def handle_output(self, hc, hn, tp, output):
        self.xai_api.get_text_signal.emit(output)
        return True
    def newhookinsert(self, pid, addr, hcode):
        pass
    @threader
    def getembedtext(self, text: str, tp):
        self.embedcallback(text, text, tp)
    def embedcallback(self, text: str, trans: str, tp: ThreadParam):
        self.Luna_embedcallback(tp, text, trans)
