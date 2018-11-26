"""versioninfo"""


# pylint: disable=too-few-public-methods
class VersionInfo:
    """Version info dataclass"""

    # pylint: disable=too-many-arguments
    def __init__(self, major: int, minor: int, build: int, level: str, serial: int):
        self.major = major
        self.minor = minor
        self.build = build
        self.level = level
        self.serial = serial

    def __str__(self):
        return '{major}.{minor}.{build}{level}{serial}'.format(**self.__dict__)


VERSION = VersionInfo(1, 0, 0, 'a', 0)
