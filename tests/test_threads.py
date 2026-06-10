from yt_dlp_plugins.extractor.threads import _shortcode_to_id


def test_shortcode_to_id():
    assert _shortcode_to_id('CuZsgfWLyiI') == '3141737961795561608'
