from enum import Enum

class VM_STATE(Enum):
    off     = 0
    on      = 1
    error   = 2
    unknown = 3

DISK_TYPES = {
    'virtio-blk': {
        'name': 'virtio-blk',
        'short': 'virtioblk',
        'description': 'Low latency virtio disk driver',
    },
    'ahci-hd': {
        'name': 'acpi-hd',
        'short': 'acpihd',
        'description': 'Acpi interface disk driver',
    },
}
NIC_TYPES = {
    'virtio-net': {
        'name': 'virtio-net',
        'short': 'virtionet',
        'description': 'Low latency virtio network driver',
    },
    'e1000': {
        'name': 'e1000',
        'short': 'e1000',
        'description': 'Intel e1000 virtual network driver',
    },
}
