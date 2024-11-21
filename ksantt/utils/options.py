from pytest import Parser


class KubeSanOptions:
    """Encapsulates pytest custom options."""

    def __init__(self, parser: Parser):
        self.parser = parser

    def storage_class_volume_group(self):
        self.parser.addoption(
            "--sc-vg",
            action="store",
            default="",
            required=True,
            help="Specify the VG name for KubeSAN StorageClass",
        )

    def storage_class_mode(self):
        self.parser.addoption(
            "--sc-mode",
            action="store",
            default="Thin",
            required=True,
            help="Specify the volume mode for KubeSAN StorageClass: Thin or Linear",
        )

    def storage_class_fstype(self):
        self.parser.addoption(
            "--sc-fstype",
            action="store",
            default="ext4",
            help="Specify the filesystem type for KubeSAN StorageClass",
        )

    def add_options(self):
        self.storage_class_volume_group()
        self.storage_class_mode()
        self.storage_class_fstype()
