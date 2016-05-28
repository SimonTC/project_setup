import os
import argparse
import sys
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.disabled = True

VERSION = '0.1'


def parse_arguments(args):
    project_name = args.name
    if len(project_name.split(' ')) > 1:
        raise ValueError()
    if args.overwrite:
        delete_project = True
        create_git = True
        create_env = True
    else:
        delete_project = args.remove
        create_git = args.git
        create_env = args.environment
    return project_name, delete_project, create_git, create_env


def create_subfolders(project_name, project_dir, sub_dirs):
    for dir_ in sub_dirs:
        os.mkdir('{}/{}'.format(project_dir, dir_))
    logger.info('Subfolders created succesfully')


def create_init_files(project_name, project_dir, package_folders):
    for dir_ in package_folders:
        init_path = '{}/{}/__init__.py'.format(project_dir, dir_)
        with open(init_path, 'w'):
            pass
    logger.info('Init files created succesfully')


def create_setup_file(project_name, project_dir):
    with open('{}/setup.py'.format(project_dir), 'w') as setup_file:
        lines = [
            "from setuptools import setup\n",
            "\n",
            "config = {\n",
            "    'description': 'My Project',\n",
            "    'author': 'Simon T. Clement',\n",
            "    'url': 'URL to get it at',\n",
            "    'download_url': 'Where to download it',\n",
            "    'author_email': 'simon.clement@gmail.com',\n",
            "    'version': '0.0dev',\n",
            "    'install_requires': ['pytest'],\n",
            "    'packages': ['{0}'],\n".format(project_name),
            "    'scripts': [],\n",
            "    'name': '{0}'\n".format(project_name),
            "}\n",
            "\n",
            "setup(**config)\n"]
        setup_file.writelines(lines)
    logger.info('setup.py created succesfully')


def create_conda_environemt_file(project_name, project_dir):
    with open('{}/environment.yml'.format(project_dir), 'w') as environment_file:
        lines = [
            'name: {}'.format(project_name),
            'dependencies:',
            '- pip',
            '- python',
            '#- anaconda'
        ]
        text = '\n'.join(lines)
        environment_file.write(text)
    logger.info('Environment file created succesfully')


def perform_bash_command(command):
    p = subprocess.run(command,
                       cwd=project_dir, check=False,
                       stderr=subprocess.PIPE,
                       universal_newlines=True)
    try:
        p.check_returncode()
    except subprocess.CalledProcessError:
        errs = p.stderr
        logger.debug(errs)
    else:
        errs = ''
    return errs


def create_conda_environment():
    logger.info('Creating conda environment')
    command_create = 'conda env create'
    errs = perform_bash_command(command_create.split())
    return errs


def delete_conda_environment(environment_name):
    command_delete = 'conda remove -n {} --all'.format(environment_name)
    errs = perform_bash_command(command_delete.split())
    return errs


def report_on_subprocess_error(errs, action):
    print('An error occured while {}'.format(action))
    print('The following error message was received:\n{}'.format(errs))


def contains_error(errs):
    return 'error' in errs.lower()


def setup_conda_environment(environment_name):
    errs = create_conda_environment()

    if contains_error(errs):
        print('Environment already exists. Do you want to overwrite it(y/[n])?')
        overwrite = input('>>')
        if overwrite.lower() == 'n':
            sys.exit()
        else:
            errs = delete_conda_environment(project_name)
            if contains_error(errs):
                report_on_subprocess_error(errs, 'deleting the environment')
                sys.exit()
            errs = create_conda_environment()
            if contains_error(errs):
                report_on_subprocess_error(errs, 'creating the environment')
                sys.exit()
    logger.info('Conda environment created succesfully')

if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Create new python project directory in your current directory',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', help="The name for the new project. "
                        "This will also be the name for the conda environment "
                        "created and the git repository")
    parser.add_argument('-r', '--remove', help="If True: If a project folder exists "
                        " with the same name, it will be removed", default=False)
    parser.add_argument('-g', '--git', help='If True: will put project under local git '
                        'version control', default=False)
    parser.add_argument('-e', '--environment', help='If True: creates a conda '
                        'environment with the same name as the project',
                        default=False)
    parser.add_argument('-o', '--overwrite', help='If True: the same as '
                        '-r True -g True -e True', default=False)

    args = parser.parse_args()
    try:
        project_name, delete_project, create_git, create_env = parse_arguments(args)
    except ValueError:
        print('Project name has to be a single word')
        sys.exit()
    logger.info('Project name: {}'.format(project_name))
    logger.info('Deleting project: {}'.format(delete_project))
    logger.info('Placing under revision: {}'.format(create_git))
    logger.info('Create conda environment: {}'.format(create_env))
    caller_dir = os.getcwd()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = '/'.join([caller_dir, project_name])
    logger.info(
        'Creating the project skeleton for {} in the folder {}'.format(
            project_name, project_dir))
    if os.path.isdir(project_dir):
        if delete_project:
            logger.info('Deleting the folder {}'.format(project_dir))
            shutil.rmtree(project_dir)
        else:
            print('Project dir already exists. Exiting the script')
            print('If you want to remove the dir. Run the script with -r True')
            sys.exit()
    # Create project dir
    os.mkdir(project_dir)
    logger.info('Directory created succesfully')
    logger.info('Project dir: {}'.format(project_dir))

    # Create sub folders
    subfolders = [project_name, 'tests']
    create_subfolders(project_name, project_dir, subfolders)

    # Create init files
    package_folders = subfolders
    create_init_files(project_name, project_dir, package_folders)

    # Create setup file
    create_setup_file(project_name, project_dir)

    if create_env:
        # Create conda environment.yml file
        create_conda_environemt_file(project_name, project_dir)

        # Create conda environment
        setup_conda_environment(project_name)

        # Create .env file to be used with autoenv to automatically activate
        # the correct environment
        with open('{}/.env'.format(project_dir), 'w') as f:
            f.write('source activate {}'.format(project_name))

    if create_git:
        # Copy the git .ignore file to project directory
        template_file = '{}/gitignore_template'.format(current_dir)
        shutil.copy(template_file, '{}/.gitignore'.format(project_dir))

        # Create readme file
        with open('{}/README.md'.format(project_dir), 'w') as f:
            lines = [
                '{}'.format(project_name),
                '==================',
                'This project is still under development.',
                'This README file has been created automatically using my '
                'project_setup.py script version {}.'.format(VERSION),
                'Usage',
                '------------',
                'To get up and running with this project just download the project'
                ' and cd into the main directory. Run the command '
                '"conda env create" and activate it afterwards with '
                '"source activate {}"'.format(project_name),
                '\nDependencies:',
                '* Anaconda - needed to setup the conda environment',
                '* (Optional) autoenv - if autoenv is installed, the environment'
                ' is automatically activated when entering the poject directory'
            ]
            text = '\n'.join(lines)
            f.write(text)
        # Make folder a git repository
        init_command = 'git init'
        errs = perform_bash_command(init_command.split())
        if contains_error(errs):
            report_on_subprocess_error(errs, 'git init')
            sys.exit()

        # Initial commit
        add_command = 'git add .'
        errs = perform_bash_command(add_command.split())
        if contains_error(errs):
            report_on_subprocess_error(errs, 'git add')
            sys.exit()
        commit_command = 'git commit -m'.split()
        commit_command.append('"initial commit"')
        errs = perform_bash_command(commit_command)
        if contains_error(errs):
            report_on_subprocess_error(errs, 'git commit')
            sys.exit()

    print('Project skeleton succesfully created')
    if create_env:
        print('To activate the environment type:')
        print('source activate {}'.format(project_name))
        print('Or cd into the directory if you have autoenv installed')
