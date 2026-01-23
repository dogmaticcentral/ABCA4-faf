
import pytest
from faf_classes.faf_analysis import FafAnalysis  # adjust import path


class ConcreteFafAnalysis(FafAnalysis):
    """Concrete implementation for testing"""

    def input_manager(self, faf_img_dict: dict):
        return []

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool):
        return ""


def test_create_args_list_with_bool_true():
    analysis = ConcreteFafAnalysis(internal_kwargs={'skip_xisting': True})
    analysis.create_parser()
    args_list = analysis._create_args_list()

    assert '--skip_xisting' in args_list


def test_create_args_list_with_bool_false_default():
    analysis = ConcreteFafAnalysis(internal_kwargs={'skip_xisting': False})
    analysis.create_parser()
    args_list = analysis._create_args_list()

    assert '--skip_xisting' not in args_list


def test_create_args_list_with_non_bool_values():
    analysis = ConcreteFafAnalysis(internal_kwargs={'n_cpus': 4, 'image_path': '/some/path'})
    analysis.create_parser()
    args_list = analysis._create_args_list()

    assert '--n-cpus' in args_list
    assert args_list[args_list.index('--n-cpus') + 1] == '4'
    assert '--image-path' in args_list
    assert args_list[args_list.index('--image-path') + 1] == '/some/path'


def test_create_args_list_invalid_argument():
    analysis = ConcreteFafAnalysis(internal_kwargs={'invalid_arg': True})
    analysis.create_parser()

    with pytest.raises(Exception, match="does not seem to be switch"):
        analysis._create_args_list()

