from setuptools import setup


setup(
    name = "javalang-ext",
    packages = ["javalang_ext"],
    version = "0.15.0",
    author = "Nevil Macwan",
    author_email = "macnev2013@gmail.com",
    url = "http://github.com/macnev2013/javalang-ext",
    description = "Pure Python Java parser and tools",
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries"
        ],
    long_description = """\
========
javalang-ext
========


`javalang-ext` builds on [javalang](https://github.com/c2nes/javalang),
which is a pure Python library for working with Java source code,
providing a lexer and parser targeting Java 8.
The implementation is based on the Java language spec available at http://docs.oracle.com/javase/specs/jls/se8/html/.
The `javalang-ext` library builds upon javalang and adds quality-of-life updates to make use easier.

""",
    zip_safe = False,
    install_requires = ['six',],
    tests_require = ["nose",],
    test_suite = "nose.collector",
)
