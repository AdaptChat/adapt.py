import pathlib
import re

from setuptools import setup

ROOT = pathlib.Path(__file__).parent

with open('adapt/__init__.py', 'r') as f:
    content = f.read()

    def extract_magic_value(name: str, *, default: str | None = None) -> str:
        try:
            return re.search(rf'^__{name}__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE).group(1)
        except AttributeError:
            if default is None:
                raise RuntimeError(f'Unable to find {name} string')
            return default

    version = extract_magic_value('version')
    author = extract_magic_value('author', default='jay3332')
    license_ = extract_magic_value('license', default='MIT')

with open(ROOT / 'README.md', encoding='utf-8') as f:
    readme = f.read()

with open(ROOT / 'requirements.txt', encoding='utf-8') as f:
    requirements = f.readlines()

setup(
    name="adapt.py",
    author=author,
    url="https://github.com/AdaptChat/adapt.py",
    project_urls={
        "Issue tracker": "https://github.com/AdaptChat/adapt.py/issues/new",
        "Documentation": "https://adaptpy.readthedocs.io/en/latest/",
        "Discord server": "https://discord.gg/5BUFNBPG",
    },
    version=version,
    packages=["adapt", "adapt.models", "adapt.types"],
    license=license_,
    description="Official wrapper around Adapt's API for Python.",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "docs": [
            "sphinx>=4.1.1",
            # "sphinx-material",
            # 'sphinx-copybutton',
            # 'readthedocs-sphinx-search',
            'furo',
        ],
        "performance": ["aiohttp[speedups]", "msgpack"],
    },
    python_requires=">=3.8.0",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Typing :: Typed',
    ],
)
