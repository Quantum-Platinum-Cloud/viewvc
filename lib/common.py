# -*-python-*-
#
# Copyright (C) 1999-2021 The ViewCVS Group. All Rights Reserved.
#
# By using this file, you agree to the terms and conditions set forth in
# the LICENSE.html file which can be found at the top level of the ViewVC
# distribution or at http://viewvc.org/license-1.html.
#
# For more information, visit http://viewvc.org/
#
# -----------------------------------------------------------------------
#
# common: common definitions for the viewvc library
#
# -----------------------------------------------------------------------

import sys
import io

# Special type indicators for diff header processing and idiff return codes
_RCSDIFF_IS_BINARY = "binary-diff"
_RCSDIFF_ERROR = "error"
_RCSDIFF_NO_CHANGES = "no-changes"


class _item:
    def __init__(self, **kw):
        vars(self).update(kw)


# Python 3: workaround for cmp()
def cmp(a, b):
    if a is None and b is None:
        return 0
    if a is None:
        return 1
    if b is None:
        return -1
    assert type(a) == type(b)
    return (a > b) - (a < b)


class TemplateData:
    """A custom dictionary-like object that allows one-time definition
    of keys, and only value fetches and changes, and key deletions,
    thereafter.

    EZT doesn't require the use of this special class -- a normal
    dict-type data dictionary works fine.  But use of this class will
    assist those who want the data sent to their templates to have a
    consistent set of keys."""

    def __init__(self, initial_data={}):
        self._items = initial_data

    def __getitem__(self, key):
        return self._items.__getitem__(key)

    def __setitem__(self, key, item):
        assert key in self._items
        return self._items.__setitem__(key, item)

    def __delitem__(self, key):
        return self._items.__delitem__(key)

    def __str__(self):
        return str(self._items)

    def keys(self):
        return self._items.keys()

    def merge(self, template_data):
        """Merge the data in TemplataData instance TEMPLATA_DATA into this
        instance.  Avoid the temptation to use this conditionally in your
        code -- it rather defeats the purpose of this class."""

        assert isinstance(template_data, TemplateData)
        self._items.update(template_data._items)


class ViewVCException(Exception):
    def __init__(self, msg, status=None):
        self.msg = msg
        self.status = status

    def __str__(self):
        if self.status:
            return "%s: %s" % (self.status, self.msg)
        return "ViewVC Unrecoverable Error: %s" % self.msg


def print_exception_data(server, exc_data):
    """Print the exception data to the server output stream.  Details are expected
    to be already HTML-escaped."""
    status = exc_data["status"]
    msg = exc_data["msg"]
    tb = exc_data["stacktrace"]

    if not server.response_started():
        server.start_response(status=status)

    fp = io.TextIOWrapper(server.file(), "utf-8", "xmlcharrefreplace", write_through=True)
    fp.write("<h3>An Exception Has Occurred</h3>\n")
    s = msg and f"<p><pre>{msg}</pre></p>" or ""
    if status:
        s = s + (f"<h4>HTTP Response Status</h4>\n<p><pre>\n{status}</pre></p><hr />\n")
    fp.write(s)
    fp.write("<h4>Python Traceback</h4>\n<p><pre>")
    fp.write(tb)
    fp.write("</pre></p>\n")


def get_exception_data():
    # Capture the exception before doing anything else.
    exc_type, exc, exc_tb = sys.exc_info()

    exc_dict = {
        "status": None,
        "msg": None,
        "stacktrace": None,
    }

    try:
        # Build a string from the formatted exception, but skipping the
        # first line.
        import traceback

        if isinstance(exc, ViewVCException):
            exc_dict["msg"] = exc.msg
            exc_dict["status"] = exc.status
        formatted = traceback.format_exception(exc_type, exc, exc_tb)
        if exc_tb is not None:
            formatted = formatted[1:]
        exc_dict["stacktrace"] = "".join(formatted)
    finally:
        # Prevent circular reference.  The documentation for sys.exc_info
        # warns "Assigning the traceback return value to a local variable
        # in a function that is handling an exception will cause a
        # circular reference..."  This is all based on 'exc_tb', and we're
        # now done with it, so toss it.
        del exc_tb

    return exc_dict
