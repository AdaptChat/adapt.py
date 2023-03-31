class StatelessAsset:
    """An asset that does not have access to any state.

    If you want to download this asset, you must manually fetch the asset data using the URL provided by this asset.
    """

    __slots__ = ('_url',)

    def __init__(self, route: str) -> None:
        pass
