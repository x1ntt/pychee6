from setuptools import setup

requirements = open("requirements.txt").read().split("\n")

setup(
    name="pychee6",
    version="0.4.7",
    description="A simple python moudle for Lychee",
    long_description_content_type="text/markdown",
    long_description=open("README.md", "rt", encoding="utf-8").read(),
    author="x1nt",
    author_email="cjdty@qq.com",
    url="https://github.com/x1ntt/pychee6",
    packages=["pychee6"],
    package_dir={"pychee6": "src"},
    include_package_data=True,
    install_requires=requirements,
    package_data={
        'pychee6': ['locales/**/*'],
    },
)
