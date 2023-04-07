from sys import version_info


if version_info < (3, 9):
    def removeprefix(self: str, prefix: str, /) -> str:
        if self.startswith(prefix):
            return self[len(prefix):]
        return self

    def removesuffix(self: str, suffix: str, /) -> str:
        if self.endswith(suffix):
            return self[:-len(suffix)]
        return self
else:
    removeprefix = str.removeprefix
    removesuffix = str.removesuffix
