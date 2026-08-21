#!/usr/bin/env python3
# macdress_probe.py
# Probe for Actaea 2.0 dressing (A2.0-5): can an UNBUNDLED python
# process rename its macOS app menu before Tk builds the menu bar?
#
# The technique under test is the community CFBundleName rewrite: reach
# NSBundle.mainBundle's infoDictionary via ctypes/objc and overwrite
# CFBundleName in memory before NSApplication snapshots it for the menu
# bar. It is not documented API, so nothing gets built on it until this
# probe shows "Actaea" in the menu bar on Stefan's machine.
#
# What it prints: the main bundle path, the concrete dictionary class,
# whether the dictionary is mutable (respondsToSelector: guards the
# write; ObjC exceptions would abort the process, so we never write
# blind), and the read-back value. Then it opens a small Tk window:
# the MENU BAR beside the apple is the verdict, not the printout.

import ctypes
import ctypes.util
import sys

if sys.platform != "darwin":
    sys.exit("darwin only")

libobjc = ctypes.CDLL(ctypes.util.find_library("objc"))
ctypes.CDLL(ctypes.util.find_library("AppKit"))  # pull in the classes

libobjc.objc_getClass.restype = ctypes.c_void_p
libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
libobjc.sel_registerName.restype = ctypes.c_void_p
libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
libobjc.object_getClassName.restype = ctypes.c_char_p
libobjc.object_getClassName.argtypes = [ctypes.c_void_p]

_MSG = ctypes.cast(libobjc.objc_msgSend, ctypes.c_void_p).value


def _cls(name):
    return libobjc.objc_getClass(name.encode())


def _sel(name):
    return libobjc.sel_registerName(name.encode())


def send(obj, selname, args=(), argtypes=(), restype=ctypes.c_void_p):
    proto = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p,
                             *argtypes)
    return proto(_MSG)(obj, _sel(selname), *args)


def nss(text):
    return send(_cls("NSString"), "stringWithUTF8String:",
                (text.encode("utf-8"),), (ctypes.c_char_p,))


def utf8(nsstr):
    if not nsstr:
        return None
    raw = send(nsstr, "UTF8String", restype=ctypes.c_char_p)
    return raw.decode("utf-8") if raw else None


def rename_in(dictionary, label):
    """Overwrite CFBundleName in one info dictionary, guarded."""
    if not dictionary:
        print("%s: absent" % label)
        return False
    kind = libobjc.object_getClassName(dictionary).decode()
    mutable = send(dictionary, "respondsToSelector:",
                   (_sel("setObject:forKey:"),), (ctypes.c_void_p,),
                   restype=ctypes.c_bool)
    before = utf8(send(dictionary, "objectForKey:", (nss("CFBundleName"),),
                       (ctypes.c_void_p,)))
    print("%s: class=%s mutable=%s CFBundleName=%r"
          % (label, kind, mutable, before))
    if not mutable:
        return False
    send(dictionary, "setObject:forKey:", (nss("Actaea"),
         nss("CFBundleName")), (ctypes.c_void_p, ctypes.c_void_p))
    after = utf8(send(dictionary, "objectForKey:", (nss("CFBundleName"),),
                      (ctypes.c_void_p,)))
    print("%s: rewrote, reads back %r" % (label, after))
    return after == "Actaea"


def main():
    bundle = send(_cls("NSBundle"), "mainBundle")
    print("mainBundle path:", utf8(send(bundle, "bundlePath")))
    wrote = rename_in(send(bundle, "infoDictionary"), "infoDictionary")
    # The menu bar prefers the localized dictionary when one exists.
    rename_in(send(bundle, "localizedInfoDictionary"),
              "localizedInfoDictionary")
    print("in-memory rewrite %s; the VERDICT is the menu bar."
          % ("succeeded" if wrote else "FAILED"))

    # Only now may Tk exist: the rewrite must precede the menu bar.
    import tkinter as tk
    root = tk.Tk()
    root.title("Actaea dressing probe")
    tk.Label(root, padx=40, pady=40, font=("Helvetica", 18),
             text="Look at the MENU BAR beside the apple.\n"
                  "Actaea = the trick works. Python = it does not.\n"
                  "Close this window when you have seen it.""").pack()
    root.mainloop()
    print("probe window closed")


if __name__ == "__main__":
    main()
