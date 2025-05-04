# neomirdata
Common loaders for Music Information Retrieval (MIR) datasets. Find the API documentation [here](https://mirdata.readthedocs.io/).

![CI status](https://github.com/probablyrobot/neomirdata/actions/workflows/ci.yml/badge.svg?branch=master)
![Formatting status](https://github.com/probablyrobot/neomirdata/actions/workflows/formatting.yml/badge.svg?branch=master)
![Linting status](https://github.com/probablyrobot/neomirdata/actions/workflows/lint-python.yml/badge.svg?branch=master)
[![Documentation Status](https://readthedocs.org/projects/neomirdata/badge/?version=latest)](https://neomirdata.readthedocs.io/en/latest/?badge=latest)
![GitHub](https://img.shields.io/github/license/probablyrobot/neomirdata.svg)


[![PyPI version](https://badge.fury.io/py/neomirdata.svg)](https://badge.fury.io/py/neomirdata)
[![codecov](https://codecov.io/gh/probablyrobot/neomirdata/branch/master/graph/badge.svg)](https://codecov.io/gh/probablyrobot/neomirdata)
[![Downloads](https://static.pepy.tech/badge/neomirdata)](https://pepy.tech/project/neomirdata)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

This library is a fork of [mirdata](https://github.com/mir-dataset-loaders/mirdata) and provides tools for working with common MIR datasets, including tools for:
* downloading datasets to a common location and format
* validating that the files for a dataset are all present 
* loading annotation files to a common format, consistent with the format required by [mir_eval](https://github.com/craffel/mir_eval)
* parsing track level metadata for detailed evaluations

### Maintainer
Igor Bogicevic (igor.bogicevic@gmail.com) - [@probablyrobot](https://github.com/probablyrobot)

### Installation

To install, simply run:

```python
pip install neomirdata
```

### Quick example
```python
import mirdata

orchset = mirdata.initialize('orchset')
orchset.download()  # download the dataset
orchset.validate()  # validate that all the expected files are there

example_track = orchset.choice_track()  # choose a random example track
print(example_track)  # see the available data
```
See the [documentation](https://mirdata.readthedocs.io/) for more examples and the API reference.


### Currently supported datasets


Supported datasets include [AcousticBrainz](https://zenodo.org/record/2553414#.X8jTgulKhhE), [DALI](https://github.com/gabolsgabs/DALI), [Guitarset](http://github.com/marl/guitarset/), [MAESTRO](https://magenta.tensorflow.org/datasets/maestro), [TinySOL](https://www.orch-idea.org/), among many others.

For the **complete list** of supported datasets, see the [documentation](https://mirdata.readthedocs.io/en/stable/source/quick_reference.html)


### Citing

This project is a fork of mirdata. When using this library, please cite both the original mirdata paper and this fork:

Original mirdata paper:
```
"mirdata: Software for Reproducible Usage of Datasets"
Rachel M. Bittner, Magdalena Fuentes, David Rubinstein, Andreas Jansson, Keunwoo Choi, and Thor Kell
in International Society for Music Information Retrieval (ISMIR) Conference, 2019
```

```
@inproceedings{
  bittner_fuentes_2019,
  title={mirdata: Software for Reproducible Usage of Datasets},
  author={Bittner, Rachel M and Fuentes, Magdalena and Rubinstein, David and Jansson, Andreas and Choi, Keunwoo and Kell, Thor},
  booktitle={International Society for Music Information Retrieval (ISMIR) Conference},
  year={2019}
}
```

When working with datasets, please cite both the original mirdata paper and include the reference of the dataset, which can be found in the respective dataset loader using the `cite()` method.

### Contributing

We welcome contributions to this library, especially new datasets. Please see [contributing](https://mirdata.readthedocs.io/en/latest/source/contributing.html) for guidelines.
