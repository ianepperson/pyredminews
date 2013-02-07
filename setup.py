from distutils.core import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name = "pyredmine",
    packages = ["redmine"],
    version = "0.2",
    extras_require = {
        },
    description = "Python Redmine Web Services Library",
    long_description = readme(),
    author = "Ian Epperson",
    author_email = "ian@epperson.com",
    url = "https://github.com/ianepperson/pyredminews",
    keywords = ["redmine", "server"],
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Groupware",
        "Topic :: Utilities",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        ],
)
