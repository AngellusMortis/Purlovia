from .common import *


def test_defaults(loader: AssetLoader):
    loader.wipe_cache()
    asset = loader[PGD_ASSETNAME]
    assert asset.is_linked
    assert asset.has_properties
    assert not asset.has_bulk_data

    loader.wipe_cache()
    with ue_parsing_context():
        asset = loader[PGD_ASSETNAME]
        assert asset.is_linked
        assert asset.has_properties
        assert not asset.has_bulk_data


def test_linking(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False):
        asset = loader[PGD_ASSETNAME]
        assert not asset.is_linked

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(link=True):
            asset = loader[PGD_ASSETNAME]
            assert asset.is_linked

    loader.wipe_cache()
    with ue_parsing_context(link=True):
        asset = loader[PGD_ASSETNAME]
        assert asset.is_linked


def test_properties(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(properties=False):
        asset = loader[PGD_ASSETNAME]
        assert not asset.has_properties

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(properties=True):
            asset = loader[PGD_ASSETNAME]
            assert asset.has_properties

    loader.wipe_cache()
    with ue_parsing_context(properties=True):
        asset = loader[PGD_ASSETNAME]
        assert asset.has_properties


def test_no_properties_without_link(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False, properties=True):
        asset = loader[PGD_ASSETNAME]
        assert not asset.has_properties


def test_bulk_data(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(bulk_data=False):
        asset = loader[PGD_ASSETNAME]
        assert not asset.has_bulk_data

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(bulk_data=True):
            asset = loader[PGD_ASSETNAME]
            assert asset.has_bulk_data

    loader.wipe_cache()
    with ue_parsing_context(bulk_data=True):
        asset = loader[PGD_ASSETNAME]
        assert asset.has_bulk_data
