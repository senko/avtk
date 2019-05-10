from os.path import dirname, join, abspath, exists
from subprocess import run

asset_root = abspath(join(dirname(__file__), '..', '..', '..', 'test-media'))


def asset_path(type, name):
    path = join(asset_root, type, name)
    if not exists(path):
        raise ValueError("asset path %s doesn't exist" % path)
    return path


def compare_images(a, b):
    """
    Compare images using ImageMagick perceptual hash

    Returns a floating point number representing difference between images.
    The score is 0 for identical images, and should be well below 1.0 for the same
    image (re)compressed with different formats/algorithms.
    """

    print(' '.join(['compare', '-metric', 'phash', a, b, 'null:']))
    proc = run(['compare', '-metric', 'phash', a, b, 'null:'], capture_output=True, text=True)
    return float(proc.stderr.strip())
