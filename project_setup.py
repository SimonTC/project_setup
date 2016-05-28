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


def load_file_to_string(file_path):
    with open(file_path, 'r')as source_file:
        lines = []
        for line in source_file:
            lines.append(line)
        source_string = ''.join(lines)
    return source_string


def create_file_from_template(file_name, value_dict, project_dir, template_dir):
    """
    Creates a file from a template saved in the templates folder.
    file_name: Name of the target file including extension.
               The name of the template file has to be the same with _template
               appended
    value_dict: dictionary containing values for the key words used in the
                template file.
    project_dir: directory where the target file is placed.
    template_dir: directory where the template file is found.
    """
    template_path = '{}/{}_template'.format(template_dir, file_name)
    raw_string = load_file_to_string(template_path)
    text = raw_string.format(**value_dict)
    with open('{}/{}'.format(project_dir, file_name), 'w') as target_file:
        target_file.write(text)
    logger.info('"{}" succesfully created'.format(file_name))


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
    template_dir = '{}/templates'.format(current_dir)
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
    create_file_from_template(file_name='setup.py',
                              value_dict={'project_name': project_name},
                              project_dir=project_dir,
                              template_dir=template_dir)

    if create_env:
        # Create conda environment.yml file
        create_file_from_template(file_name='environment.yml',
                                  value_dict={'project_name': project_name},
                                  project_dir=project_dir,
                                  template_dir=template_dir)

        # Create conda environment
        setup_conda_environment(project_name)

        # Create .env file to be used with autoenv to automatically activate
        # the correct environment
        with open('{}/.env'.format(project_dir), 'w') as f:
            f.write('source activate {}'.format(project_name))

    if create_git:
        # Copy the git .ignore file to project directory
        template_file = '{}/gitignore_template'.format(template_dir)
        shutil.copy(template_file, '{}/.gitignore'.format(project_dir))

        # Create readme file
        create_file_from_template(file_name='README.md',
                                  value_dict={'project_name': project_name},
                                  project_dir=project_dir,
                                  template_dir=template_dir)

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
