import os

def get_user_choices():
    """
    Prompts the user for project directory, subjects, nights, and set file patterns.
    Returns:
        project_dir (str): Path to the project directory
        selected_subjects (list or str): List of subject folder names (or "all")
        selected_nights (list or str): List of night folder names (or "all")
        set_templates (list): List of .set file patterns (or filenames) to look for
    """

    # ---- A) Prompt for Project Directory ----
    project_dir = input("Enter the path to your project directory: ").strip()
    while not os.path.isdir(project_dir):
        print(f"Directory '{project_dir}' not found. Please try again.")
        project_dir = input("Enter the path to your project directory: ").strip()

    print(f"\nProject directory set to: {project_dir}\n")

    # ---- B) Show available subjects ----
    subjects_dirs = [
        d for d in os.listdir(project_dir)
        if os.path.isdir(os.path.join(project_dir, d))
    ]

    if not subjects_dirs:
        print(f"No subject directories found in project directory: {project_dir}")
        return project_dir, [], [], []

    print("Available Subjects:")
    for i, subject in enumerate(subjects_dirs, 1):
        print(f"{i}. {subject}")
    print(f"{len(subjects_dirs) + 1}. All Subjects")

    subject_choice = input("Enter the number(s) for the subject(s) you want to process (e.g., '1,2') or select 'All': ").strip()

    if subject_choice == str(len(subjects_dirs) + 1) or subject_choice.lower() == "all":
        selected_subjects = "all"
    else:
        selected_indices = [int(x) for x in subject_choice.split(",") if x.isdigit()]
        selected_subjects = [subjects_dirs[i - 1] for i in selected_indices if 0 < i <= len(subjects_dirs)]
        if not selected_subjects:
            print("No valid subjects were selected. Exiting.")
            return project_dir, [], [], []

    # ---- C) Show available nights (for each chosen subject) ----
    all_nights = set()
    for subj in subjects_dirs if selected_subjects == "all" else selected_subjects:
        subj_dir = os.path.join(project_dir, subj)
        nights = [
            d for d in os.listdir(subj_dir)
            if os.path.isdir(os.path.join(subj_dir, d))
        ]
        all_nights.update(nights)

    if not all_nights:
        print(f"No night folders found for the selected subject(s). Exiting.")
        return project_dir, [], [], []

    all_nights = sorted(all_nights)
    print("\nAvailable Nights:")
    for i, night in enumerate(all_nights, 1):
        print(f"{i}. {night}")
    print(f"{len(all_nights) + 1}. All Nights")

    night_choice = input("Enter the number(s) for the night(s) you want to process (e.g., '1,2') or select 'All': ").strip()

    if night_choice == str(len(all_nights) + 1) or night_choice.lower() == "all":
        selected_nights = "all"
    else:
        selected_indices = [int(x) for x in night_choice.split(",") if x.isdigit()]
        selected_nights = [all_nights[i - 1] for i in selected_indices if 0 < i <= len(all_nights)]
        if not selected_nights:
            print("No valid nights were selected. Exiting.")
            return project_dir, [], [], []

    # ---- D) Gather and show available .set files ----
    print("\nGathering available .set files based on your chosen subjects and nights...")

    set_files_across_selection = set()
    actual_subjects = subjects_dirs if selected_subjects == "all" else selected_subjects

    for subj in actual_subjects:
        subj_dir = os.path.join(project_dir, subj)
        possible_nights = [
            d for d in os.listdir(subj_dir)
            if d in selected_nights or selected_nights == "all"
        ]
        for night in possible_nights:
            night_dir = os.path.join(subj_dir, night)
            files_in_night = os.listdir(night_dir) if os.path.isdir(night_dir) else []
            for fname in files_in_night:
                if fname.lower().endswith(".set"):
                    set_files_across_selection.add(fname)

    set_files_across_selection = sorted(set_files_across_selection)

    if not set_files_across_selection:
        print("No .set files found in the chosen subjects/nights.")
        set_templates = ["*.set"]  # Default to process all .set files
    else:
        print("\nAvailable .set files:")
        for i, fname in enumerate(set_files_across_selection, 1):
            print(f"{i}. {fname}")
        print(f"{len(set_files_across_selection) + 1}. All .set Files")

        set_choice = input("Enter the number(s) for the .set files to process (e.g., '1,2') or select 'All': ").strip()

        if set_choice == str(len(set_files_across_selection) + 1) or set_choice.lower() == "all":
            set_templates = ["*.set"]
        else:
            selected_indices = [int(x) for x in set_choice.split(",") if x.isdigit()]
            set_templates = [set_files_across_selection[i - 1] for i in selected_indices if 0 < i <= len(set_files_across_selection)]
            if not set_templates:
                print("No valid .set files were selected. Exiting.")
                return project_dir, [], [], []

    # ---- Summary ----
    print("\nUser inputs collected successfully.")
    print(f"Project Dir: {project_dir}")
    print(f"Subjects:    {selected_subjects}")
    print(f"Nights:      {selected_nights}")
    print(f".set files:  {set_templates}\n")

    return project_dir, selected_subjects, selected_nights, set_templates
