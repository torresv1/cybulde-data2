from pathlib import Path
from subprocess import CalledProcessError

from cybulde.utils.utils import get_logger, run_shell_command

DATA_UTILS_LOGGER = get_logger(Path(__file__).name)


def is_dvc_initialized() -> bool:
    return (Path().cwd() / ".dvc").exists()


def initialize_dvc() -> None:
    if is_dvc_initialized():
        DATA_UTILS_LOGGER.info("DVC is already initialized.")
        return

    DATA_UTILS_LOGGER.info("Initializing DVC...")
    run_shell_command("dvc init")
    run_shell_command("dvc config core.analytics false")
    run_shell_command("dvc config core.autostage true")
    run_shell_command("git add .dvc")
    run_shell_command("git commit -nm 'Initialized DVC'")


def initialize_dvc_storage(dvc_remote_name: str, dvc_remote_url: str) -> None:
    existing_remotes = run_shell_command("dvc remote list").strip()
    if dvc_remote_name not in existing_remotes:
        DATA_UTILS_LOGGER.info("Initializing DVC storage...")
        run_shell_command(f"dvc remote add -d {dvc_remote_name} {dvc_remote_url}")
        run_shell_command("git add .dvc/config")
        run_shell_command(f"git commit -nm 'Configured remote storage at: {dvc_remote_url}'")
    else:
        DATA_UTILS_LOGGER.info("DVC storage was already initialized.")
        return


def commit_to_dvc(dvc_raw_data_folder: str, dvc_remote_name: str) -> None:
    # Get all tags and find the highest version number
    tags_output = run_shell_command("git tag --list").strip()
    if tags_output:
        tags = [tag.strip() for tag in tags_output.split("\n") if tag.strip().startswith("v")]
        versions = []
        for tag in tags:
            try:
                version_num = int(tag[1:])  # Remove 'v' prefix and convert to int
                versions.append(version_num)
            except ValueError:
                continue
        current_version = str(max(versions)) if versions else "0"
    else:
        current_version = "0"
    next_version = f"v{int(current_version) + 1}"
    run_shell_command(f"dvc add {dvc_raw_data_folder}")
    run_shell_command("git add .")
    run_shell_command(f"git commit -nm 'Updated version of the data from " f"v{current_version} to {next_version}'")
    run_shell_command(f"git tag -a {next_version} -m 'Data version {next_version}'")
    run_shell_command(f"dvc push {dvc_raw_data_folder}.dvc " f"--remote {dvc_remote_name}")
    run_shell_command("git push --follow-tags")
    run_shell_command("git push -f --tags")


def make_new_data_version(dvc_raw_data_folder: str, dvc_remote_name: str) -> None:
    dvc_file = f"{dvc_raw_data_folder}.dvc"
    dvc_file_exists = Path(dvc_file).exists()

    if not dvc_file_exists:
        DATA_UTILS_LOGGER.info(f"No DVC file found at {dvc_file}. Creating initial version...")
        commit_to_dvc(dvc_raw_data_folder, dvc_remote_name)
        return
    try:
        status = run_shell_command(f"dvc status {dvc_file}").strip()
        if "Data and pipelines are up to date" in status:
            DATA_UTILS_LOGGER.info("Data and pipelines are up to date.")
            return
        DATA_UTILS_LOGGER.info(f"DVC status: {status}")
        commit_to_dvc(dvc_raw_data_folder, dvc_remote_name)
    except CalledProcessError as e:
        DATA_UTILS_LOGGER.error(f"Error checking DVC status: {e}")
        commit_to_dvc(dvc_raw_data_folder, dvc_remote_name)
