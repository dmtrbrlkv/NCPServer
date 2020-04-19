from setuptools import setup

setup(
    name='NCPServer',
    version='0.1',
    scripts=['app\\app.py', 'app\\utils.py', 'config.json', 'config_example.json'],
    url='https://github.com/dmtrbrlkv/NCPServer',
    license='',
    author='Dmitry Burlakov',
    author_email='dmtrbrlkv@gmail.com',
    description='Simple server based on Flask and NotesComPy library,',
    install_requires=['Flask'],

    entry_points={
        'console_scripts': [
            'nspserver=app:main',
        ],
    }

)
