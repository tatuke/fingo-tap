from setuptools import setup

setup(
    name='ai-shell',
    version='0.1.0',
    py_modules=['ai_shell'],
    install_requires=[
        'openai',
        'prompt_toolkit',   
    ],
    entry_points={
        'console_scripts': [
            'ai=ai_shell:main',
        ],
    },
)