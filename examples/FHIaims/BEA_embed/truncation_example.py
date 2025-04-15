from embasi.embedding import ProjectionEmbedding
from embasi.parallel_utils import root_print
from ase.io import read
from ase.calculators.aims import Aims
import os
import time

'''
An example for running QM/QM embedding simulations with a truncated
basis for the high-level calculations for a nonanol molecule. The
OH fragment is calculated at the higher level of theory (PBE0), and
the hydrocarbon chain is calculated at the lower level of theory (PBE).

Basis truncation removes basis centers which contribute a negligible
amount of charge to the embedded subsystem, thereby reducing the
computational cost. If any real time savings are to be realised
with QM/QM embedding, basis truncation is vital to reduce the cost
incurred by including extra basis functions (either through
integration, or evaluation of nonlocal matrix quantities).

To run this example you will need to:
- Set environmental variable 'ASI_LIB_PATH' to the location of
  the FHIaims shared object library
- Set environmental variable 'AIM_SPECIES_DIR' to the location of
  your desired basis set
'''

# One may also use an environmental variable to achieve this
#os.environ['ASI_LIB_PATH'] = "/home/gabrielbramley/Software/FHIaims/_build_embasi/libaims.250403.scalapack.mpi.so"
#os.environ['AIMS_SPECIES_DIR'] = "/home/gabrielbramley/Software/FHIaims/species_defaults/defaults_2020/light/"

# root_print ensures only head node prints
try:
    root_print(f"FHIaims library: {os.environ['ASI_LIB_PATH']}")
except:
    raise "Please set the environmental variable: ASI_LIB_PATH"

try:
    root_print(f"Basis directory: {os.environ['AIMS_SPECIES_DIR']}")
except:
    raise "Please set the environmental variable: AIMS_SPECIES_DIR"


# Set-up calculator parameters (similar to FHIaims Calculator for
# ASE) for low-level and high-level calculations. Below are the
# absolute minimum parameters required for normal operation.
from ase.calculators.aims import AimsProfile
from ase.calculators.aims import AimsCube
#water_cube = AimsCube(points=(150, 150, 150),
#                      plots=('total_density',
#                             'delta_density',),)
                      #origin=(-2.5,-0.5,0.),
                      #edges=[(9.0,0.,0.),
                      #       (0.,3.5,0.),
                      #       (0.,0.,2.5)])
calc_ll = Aims(xc='PBE', profile=AimsProfile(command="NOCALC"),
    KS_method="parallel",
    RI_method="LVL",
    collect_eigenvectors=True,
    density_update_method='density_matrix', # for DM export
    atomic_solver_xc="PBE",
    compute_kinetic=True,
    override_initial_charge_check=True,
#    cubes=water_cube
  )

calc_hl = Aims(xc='PBE0', profile=AimsProfile(command="NOCALC"),
    KS_method="parallel",
    RI_method="LVL",
    collect_eigenvectors=True,
    density_update_method='density_matrix', # for DM export
    atomic_solver_xc="PBE",
    compute_kinetic=True,
    override_initial_charge_check=True,
#    cubes=water_cube
  )

# Read nonanol geometry and set-up embedding mask
zeolite = read("zeolite.xyz")
embed_mask = len(nonanol)*[2]
embed_mask[4], embed_mask[5] = 1, 1
embed_mask[12], embed_mask[13] = 1, 1
embed_mask[20] = 1

# Set-up directories
os.makedirs('zeolite_exampple', exist_ok=True)

root_print('\nRunning full basis Sn subsituted zeolite \n')

os.chdir('zeolite_example')
Projection = ProjectionEmbedding(zeolite,
                                 embed_mask=embed_mask,
                                 calc_base_ll=calc_ll,
                                 calc_base_hl=calc_hl,
                                 mu_val=1.e+6,
                                 localisation="SPADE",
                                 projection="huzinaga",)
start = time.time()

# Now run the simulation!
Projection.run()

end = time.time()
fullbasis_walltime = end - start
fullbasis_energy = Projection.DFT_AinB_total_energy
root_print('Finished running full basis Sn subsituted zeolite  \n')

os.chdir('..')
