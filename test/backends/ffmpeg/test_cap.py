from avtk.backends.ffmpeg import cap


def test_get_ffmpeg_version():
    result = cap.get_ffmpeg_version()
    assert result != ""


def test_get_ffprobe_version():
    result = cap.get_ffprobe_version()
    assert result != ""


def test_get_available_codecs():
    # Using PNG, WAV and SRT for checks as these are likely to be available anywhere

    codecs = cap.get_available_codecs()

    assert 'png' in codecs
    png = codecs['png']
    assert png.type == cap.Codec.TYPE_VIDEO
    assert png.can_encode
    assert png.can_decode

    assert 'pcm_s16le' in codecs
    wav = codecs['pcm_s16le']
    assert wav.type == cap.Codec.TYPE_AUDIO
    assert wav.can_encode
    assert wav.can_decode

    assert 'srt' in codecs
    srt = codecs['srt']
    assert srt.type == cap.Codec.TYPE_SUBTITLE


def test_get_available_formats():
    # Using OGG for check as it is likely available anywhere

    formats = cap.get_available_formats()
    assert 'ogg' in formats
    ogg = formats['ogg']
    assert ogg.can_mux
    assert ogg.can_demux


def test_get_availble_encoders():
    # Using libtheora for check as it is likely available everywhere

    encoders = cap.get_available_encoders()
    assert 'libtheora' in encoders
