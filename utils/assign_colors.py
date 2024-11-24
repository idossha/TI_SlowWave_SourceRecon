
import gmsh
import csv

# Initialize Gmsh
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

# Open your mesh file
gmsh.open("HCP.msh")

# Path to your .txt file
txt_file_path = "HCP.txt"  # Replace with your actual file name

# Dictionary to store color assignments and names
assignments = {}

# Read the .txt file
with open(txt_file_path, 'r') as file:
    reader = csv.reader(file, delimiter='\t')  # Use '\t' for tab-delimited, ',' for comma-delimited
    header = next(reader)  # Skip the header line if present
    for row in reader:
        if len(row) < 6:
            continue  # Skip incomplete lines
        # Extract data
        No = int(row[0].strip())
        Label = row[1].strip()
        R = int(row[2].strip())
        G = int(row[3].strip())
        B = int(row[4].strip())
        A = int(row[5].strip())  # Alpha value, can be ignored
        # Store in the dictionary
        assignments[No] = {'Label': Label, 'R': R, 'G': G, 'B': B}

# Assign names and colors to physical groups
for No, data in assignments.items():
    Label = data['Label']
    R = data['R']
    G = data['G']
    B = data['B']
    
    # Assign the name to the physical group
    gmsh.model.setPhysicalName(3, No, Label)
    
    # Assign the color to the physical group
    gmsh.model.setColor([(3, No)], R, G, B)
    
    # Optionally, print to verify
    # print(f"Assigned name '{Label}' and color ({R}, {G}, {B}) to Physical Volume {No}")

# Set display options
gmsh.option.setNumber("Mesh.VolumeEdges", 1)
gmsh.option.setNumber("Mesh.VolumeFaces", 1)
gmsh.option.setNumber("Mesh.SurfaceEdges", 0)
gmsh.option.setNumber("Mesh.SurfaceFaces", 0)

# Run the GUI
gmsh.fltk.run()

# Finalize Gmsh
gmsh.finalize()

