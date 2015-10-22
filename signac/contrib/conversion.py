import logging


logger = logging.getLogger(__name__)

WEIGHT_DEFAULT = 1
WEIGHT_DISCOURAGED = 10
WEIGHT_STRONGLY_DISCOURAGED = 100


class AdapterMetaType(type):

    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            cls.registry = dict()
        else:
            identifier = "{}_to_{}".format(cls.expects, cls.returns)
            cls.registry[identifier] = cls

        super().__init__(name, bases, dct)


class Adapter(metaclass=AdapterMetaType):
    expects = None
    returns = None
    weight = WEIGHT_DEFAULT

    def __call__(self, x):
        assert isinstance(x, self.expects)
        return self.convert(x)

    def convert(self, x):
        return self.returns(x)

    def __str__(self):
        return "{n}(from={f},to={t})".format(
            n=self.__class__,
            f=self.expects,
            t=self.returns)

    def __repr__(self):
        return str(self)


def make_adapter(src, dst, convert=None, w=None):
    class BasicAdapter(Adapter):
        expects = src
        returns = dst
        if w is not None:
            weight = w
        if convert is not None:
            def __call__(self, x):
                return convert(x)
    return BasicAdapter