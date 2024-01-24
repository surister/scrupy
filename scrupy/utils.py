class unset:
    """
    Sentinel object singleton to describe a parameter that has not been explicitly set by the user
    """

    def __bool__(self):
        raise Exception(
            "Don't use boolean operators for unset, check identity with 'is', ie: myvar is UNSET")

    def __repr__(self):
        return str(self.__class__)


UNSET = unset()
