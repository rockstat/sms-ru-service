from collections import namedtuple


class ServiceId(namedtuple("ServiceId", ["service", "id"])):
    __slots__ = ()

    def __str__(self):
        return self.service + ':' + str(self.id)

    @classmethod
    def from_str(cls, value):
        return cls(*value.split(':'))
