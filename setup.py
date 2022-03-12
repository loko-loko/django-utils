from setuptools import setup

setup(
    name="django_utils",
    version="1.0.0",
    description="Tools for django",
    url="https://github.com/loko-loko/django-utils.git",
    author="loko-loko",
    author_email="loko-loko@github.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["django_utils"],
    include_package_data=True,
    install_requires=[
        "asn1crypto==0.24.0",
        "bcrypt==3.1.5",
        "cffi==1.11.5",
        "cryptography>=2.5",
        "paramiko==2.6.0",
        "Django==2.2.13",
        "django-ckeditor==5.6.1",
        "django-js-asset==1.1.0",
        "idna==2.8",
        "loguru==0.4.0",
        "Pillow==9.0.1",
        "psycopg2==2.7.6.1",
        "pyasn1==0.4.4",
        "pycparser==2.19",
        "PyNaCl==1.3.0",
        "pytz==2018.7",
        "six==1.12.0",
        "uWSGI==2.0.18",
        "Markdown==3.1.1",
        "boto3==1.11.9",
        "scp==0.13.2"
    ],
    entry_points={
        "console_scripts": [
            "django_utils=django_utils.__main__:main",
        ]
    },
)
