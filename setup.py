from setuptools import setup, find_packages

setup(
    name="streamfix",
    version="1.0.0",
    description="OpenAI-compatible JSON repair proxy for reliable AI responses",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="StreamFix",
    url="https://github.com/rozetyp/streamfix",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "httpx>=0.25.0",
        "jsonschema>=4.19.0",
    ],
    entry_points={
        "console_scripts": [
            "streamfix=app.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8+",
    ],
    python_requires=">=3.8",
)