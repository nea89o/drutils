from setuptools import setup

with open('drutils/version.py') as f:
    _loc = {}
    exec(f.read(), _loc, _loc)
    version = _loc['VERSION']

dev_requirements = [
    "pylint", "aiounittest", "tox", "pytest"
]

with open('README.md') as f:
    readme = f.read()

if not version:
    raise RuntimeError('version is not set in drutils/version.py')

setup(
    name="drutils",
    author="romangraef",
    url="https://github.com/romangraef/drutils",
    version=str(version),
    install_requires=[],
    long_description=readme,
    setup_requires=[],
    tests_require=dev_requirements,
    dependency_links=[''],
    license="MIT",
    packages=['drutils'],
    description="discord.py utils i found myself using often",
    classifiers=[
        'Topic :: Utilities',
    ]
)
