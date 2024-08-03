import setuptools 

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(     
     name='resource_lock',
     version='0.3.0',    
     description='Python module to lock an arbitary resource',
     long_description=long_description,
     long_description_content_type='text/markdown',
     url='https://github.com/robertblackwell/resource_lock',
     author='robertblackwell',
     author_email='',
     license='BSD 2-clause',
     packages=['resource_lock'],
     install_requires=[],
)