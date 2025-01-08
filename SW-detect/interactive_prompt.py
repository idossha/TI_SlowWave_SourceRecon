
# prompter.py

import os
import sys
import logging
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def get_user_choices():
    """
    Prompts the user for project directory, subjects, nights, and set file patterns.
    Returns:
        project_dir (str): Path to the project directory
        selected_subjects (list or str): List of subject folder names (or "all")
        selected_nights (list or str): List of night folder names (or "all")
        set_templates (list): List of .set file patterns (or filenames) to look for
    """

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    # ---- A) Prompt for Project Directory ----
    while True:
        project_dir = input(Fore.CYAN + "Enter the path to your project directory: " + Style.RESET_ALL).strip()
        if os.path.isdir(project_dir):
            logger.info(f"Project directory set to: {project_dir}\n")
            break
        else:
            logger.warning(Fore.RED + f"Directory '{project_dir}' not found. Please try again.\n" + Style.RESET_ALL)

    # ---- B) Show available subjects ----
    try:
        subjects_dirs = [
            d for d in os.listdir(project_dir)
            if os.path.isdir(os.path.join(project_dir, d))
        ]
        subjects_dirs.sort(key=lambda x: x.lower())  # Sort alphabetically
    except Exception as e:
        logger.error(Fore.RED + f"Error accessing project directory: {e}" + Style.RESET_ALL)
        return project_dir, [], [], []

    if not subjects_dirs:
        logger.error(Fore.RED + f"No subject directories found in project directory: {project_dir}" + Style.RESET_ALL)
        return project_dir, [], [], []

    print(Fore.GREEN + "Available Subjects:" + Style.RESET_ALL)
    for i, subject in enumerate(subjects_dirs, 1):
        print(f"{i}. {subject}")
    print(f"{len(subjects_dirs) + 1}. All Subjects\n")

    while True:
        subject_choice = input(Fore.CYAN + "Enter the number(s) for the subject(s) you want to process (e.g., '1,2') or type 'All': " + Style.RESET_ALL).strip()
        if subject_choice.lower() == "all" or subject_choice == str(len(subjects_dirs) + 1):
            selected_subjects = "all"
            break
        else:
            try:
                selected_indices = [int(x) for x in subject_choice.split(",")]
                if not selected_indices:
                    raise ValueError
                selected_subjects = [subjects_dirs[i - 1] for i in selected_indices if 0 < i <= len(subjects_dirs)]
                if not selected_subjects:
                    raise ValueError
                break
            except ValueError:
                logger.warning(Fore.RED + "Invalid input. Please enter valid numbers separated by commas or 'All'." + Style.RESET_ALL)

    # ---- C) Show available nights (for each chosen subject) ----
    try:
        all_nights = set()
        actual_subjects = subjects_dirs if selected_subjects == "all" else selected_subjects

        for subj in actual_subjects:
            subj_dir = os.path.join(project_dir, subj)
            nights = [
                d for d in os.listdir(subj_dir)
                if os.path.isdir(os.path.join(subj_dir, d))
            ]
            all_nights.update(nights)

        if not all_nights:
            logger.error(Fore.RED + "No night folders found for the selected subject(s). Exiting." + Style.RESET_ALL)
            return project_dir, selected_subjects, [], []

        all_nights = sorted(all_nights, key=lambda x: x.lower())  # Sort alphabetically
    except Exception as e:
        logger.error(Fore.RED + f"Error accessing nights directories: {e}" + Style.RESET_ALL)
        return project_dir, selected_subjects, [], []

    print(Fore.GREEN + "\nAvailable Nights:" + Style.RESET_ALL)
    for i, night in enumerate(all_nights, 1):
        print(f"{i}. {night}")
    print(f"{len(all_nights) + 1}. All Nights\n")

    while True:
        night_choice = input(Fore.CYAN + "Enter the number(s) for the night(s) you want to process (e.g., '1,2') or type 'All': " + Style.RESET_ALL).strip()
        if night_choice.lower() == "all" or night_choice == str(len(all_nights) + 1):
            selected_nights = "all"
            break
        else:
            try:
                selected_indices = [int(x) for x in night_choice.split(",")]
                if not selected_indices:
                    raise ValueError
                selected_nights = [all_nights[i - 1] for i in selected_indices if 0 < i <= len(all_nights)]
                if not selected_nights:
                    raise ValueError
                break
            except ValueError:
                logger.warning(Fore.RED + "Invalid input. Please enter valid numbers separated by commas or 'All'." + Style.RESET_ALL)

    # ---- D) Gather and show available .set files ----
    logger.info("\nGathering available .set files based on your chosen subjects and nights...")

    set_files_across_selection = set()
    try:
        for subj in actual_subjects:
            subj_dir = os.path.join(project_dir, subj)
            nights_to_check = all_nights if selected_nights == "all" else selected_nights
            for night in nights_to_check:
                night_dir = os.path.join(subj_dir, night)
                if not os.path.isdir(night_dir):
                    continue
                try:
                    files_in_night = os.listdir(night_dir)
                except Exception as e:
                    logger.warning(Fore.YELLOW + f"Could not access directory '{night_dir}': {e}" + Style.RESET_ALL)
                    continue
                for fname in files_in_night:
                    if fname.lower().endswith(".set"):
                        set_files_across_selection.add(fname)

        set_files_across_selection = sorted(set_files_across_selection, key=lambda x: x.lower())  # Sort alphabetically
    except Exception as e:
        logger.error(Fore.RED + f"Error while gathering .set files: {e}" + Style.RESET_ALL)
        return project_dir, selected_subjects, selected_nights, []

    if not set_files_across_selection:
        logger.warning(Fore.YELLOW + "No .set files found in the chosen subjects/nights." + Style.RESET_ALL)
        set_templates = ["*.set"]  # Default to process all .set files
    else:
        print(Fore.GREEN + "\nAvailable .set Files:" + Style.RESET_ALL)
        for i, fname in enumerate(set_files_across_selection, 1):
            print(f"{i}. {fname}")
        print(f"{len(set_files_across_selection) + 1}. All .set Files\n")

        while True:
            set_choice = input(Fore.CYAN + "Enter the number(s) for the .set files to process (e.g., '1,2') or type 'All': " + Style.RESET_ALL).strip()
            if set_choice.lower() == "all" or set_choice == str(len(set_files_across_selection) + 1):
                set_templates = ["*.set"]
                break
            else:
                try:
                    selected_indices = [int(x) for x in set_choice.split(",")]
                    if not selected_indices:
                        raise ValueError
                    set_templates = [set_files_across_selection[i - 1] for i in selected_indices if 0 < i <= len(set_files_across_selection)]
                    if not set_templates:
                        raise ValueError
                    break
                except ValueError:
                    logger.warning(Fore.RED + "Invalid input. Please enter valid numbers separated by commas or 'All'." + Style.RESET_ALL)

    # ---- Summary ----
    print(Fore.MAGENTA + "\nUser inputs collected successfully." + Style.RESET_ALL)
    print(f"{Fore.BLUE}Project Dir: {Style.RESET_ALL}{project_dir}")
    print(f"{Fore.BLUE}Subjects:    {Style.RESET_ALL}{selected_subjects}")
    print(f"{Fore.BLUE}Nights:      {Style.RESET_ALL}{selected_nights}")
    print(f"{Fore.BLUE}.set files:  {Style.RESET_ALL}{set_templates}\n")

    return project_dir, selected_subjects, selected_nights, set_templates


# Example usage (this part can be removed or commented out in production)
if __name__ == "__main__":
    project_dir, subjects, nights, set_files = get_user_choices()
    # Further processing can be done here based on the collected inputs

