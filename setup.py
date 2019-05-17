import setuptools

setuptools.setup(
    name = "zb-restqa",
    version = "0.0.3",
    license='MIT',
    author = "Manjunath Somashekar",
    author_email = "ujnamss@gmail.com",
    packages = ["zb_restqa"],
    description = "A package containing the framework for REST API testing",
    url = "http://pypi.python.org/pypi/zb-restqa/",
    keywords = ["Automation", "REST", "API", "QA", "Declarative", "Framework"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    long_description = """\
A package containing the framework for REST API testing
-----------------------------------------------------

This version requires Python 2.7 or later
""",
    install_requires=[
        "requests",
        "slackclient",
        "future>=0.16.0",
        "configparser",
        "zb_common",
        "jmespath",
        "PyYAML"
    ],
)
