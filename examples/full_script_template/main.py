import os
import gmsh
import allsolve

api_key = os.environ["QS_ACCESS_KEY"]
api_secret = os.environ["QS_SECRET_KEY"]
allsolve.setup(
    api_key=api_key,
    api_secret=api_secret,
    host="https://allsolve.quanscient.com",
)

gmsh.initialize()
gmsh.open("cube.geo")
gmsh.model.mesh.generate()
gmsh.write("cube.msh")
gmsh.finalize()

# Load the project
project = allsolve.Project.from_token()

print("Project: {}".format(project.name))

# Remove all existing files in the project. This can
# be removed if you're satisfied with the mesh and it
# doesn't need to be reuploaded.
allfiles = project.get_files()
for file in allfiles:
    allsolve.delete_file(file)

meshfile = project.add_shared_file("cube.msh")

sims = project.get_simulations()

# We have predefined the first simulation in the GUI, so it can be used as a template:
sim = allsolve.Simulation.copy_simulation(simulation_id=sims[0].id)

# Add your custom simulation scripts, as many as you need. The directory structure
# won't be preserved, but all files are loaded to the same folder in the simulation
# worker nodes. Parameter "is_main" defaults to False.
sim.set_scripts(
    [
        allsolve.Script("sim/main.py", is_main=True),
    ]
)

# Select your simulation runtime configuration, ie. node count and type. Note that
# allsolve.CPU.CORES_3_10GB_FAST_START cannot be run with more than 1 node.
sim.set_runtime(
    allsolve.Runtime(
        node_count=1,
        node_type=allsolve.CPU.CORES_1_16GB,
    )
)

# Tell the simulation to use the previously added shared mesh
sim.set_shared_files([meshfile])

# You can add parameters on the fly via files like this, only
# for this single simulation:
sim.add_json_file(
    "material_params.json",
    {
        "density": {
            "air": 1.293,
            "steel": 7850,
        },
        "speedofsound": {
            "air": 340,
            "steel": 5000,
        },
    },
)
#
# Then in the simulation script read the json file
# "material_params.json" to get the values.

sim.start()

# Wait until simulation is in one of the end states
while sim.is_running(refresh_delay_s=1):
    sim.print_new_loglines()  # prints new log lines live

sim.print_new_loglines()  # print remaining new log lines if any

# Print status without refreshing it, to check for success
print(sim.get_status())

# You can get values added with `setoutputvalue()` calls using
print(sim.get_output_values())

# To save VTUs use
#
sim.save_output_field("p harmonic 2")
#
# Use named paremeter "output_dir" if you want to save the field files
# (all ranks as separate VTUs) to other folder than "./"

# To save a modified / deformed mesh, use setoutputmesh() function on the
# simulation side and save with
# sim.save_output_mesh("meshname")

# You can save any other files you might have written:
# Also takes the optional "output_dir" parameter.
sim.save_output_files(["Test_file.txt"])

# Cleanup the sim after downloading results:
sim.delete()
