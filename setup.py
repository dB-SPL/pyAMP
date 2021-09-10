import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyAMP",
    version="0.0.6",
    author="dB-SPL",
    author_email="",
    description="Python implementation of the Amateur Multicast Protocol (AMP-2) Version 3.0 as used by FLAMP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dB-SPL/pyAMP",
	keywords=['flamp', 'fldigi', 'Python', 'Opensource'],
    packages=setuptools.find_packages(),
	install_requires=[
		'crcmod',
		'PySimpleGUI',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
