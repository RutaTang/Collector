from setuptools import setup

setup(
    name="collector",
    version='0.0.1',
    py_modules=['collector'],
    install_requires=[
        'Click'
    ],
    entry_points='''
        [console_scripts]
        collector=collector:cli
        ''',
)
