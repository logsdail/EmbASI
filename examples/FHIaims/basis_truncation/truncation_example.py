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
os.environ['ASI_LIB_PATH'] = "/home/gabrielbramley/Software/FHIaims/builds/gnu_scalapack_embedding_lib_14082024/libaims.240813.scalapack.mpi.so"

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
calc_ll = Aims(xc='PBE',
    KS_method="parallel",
    RI_method="LVL",
    collect_eigenvectors=True,
    density_update_method='density_matrix', # for DM export
    atomic_solver_xc="PBE",
    compute_kinetic=True,
  )

calc_hl = Aims(xc='PBE0',
    KS_method="parallel",
    RI_method="LVL",
    collect_eigenvectors=True,
    density_update_method='density_matrix', # for DM export
    atomic_solver_xc="PBE",
    compute_kinetic=True,
  )

# Read nonanol geometry and set-up embedding mask
nonanol = read("nonanol.xyz")
embed_mask = len(nonanol)*[2]
embed_mask[0], embed_mask[29] = 1, 1

# Set-up directories
os.makedirs('nonanol_truncated', exist_ok=True)
os.makedirs('nonanol_fullbasis', exist_ok=True)

os.chdir('nonanol_truncated')

# Set up ProjectionEmbedding, with:
# - Embedding mask (1=Highlevel (PBE0), 2=Low-level (PBE))
# - Assigned higher and lower level calculators
# - Fragment charge (Usually -1 per split covalent bond)
# - TODO: ADD AUTOMATIC DETECTION OF FRAGMENT CHARGE
Projection = ProjectionEmbedding(nonanol,
                                 embed_mask=embed_mask,
                                 calc_base_ll=calc_ll,
                                 calc_base_hl=calc_hl,
                                 mu_val=1.e+6,
                                 truncate_basis=True)

root_print('\nRunning truncated basis nonanol \n')
start = time.time()

# Now run the simulation!
Projection.run()

end = time.time()
truncated_walltime = end - start
truncated_energy = Projection.DFT_AinB_total_energy
root_print('Finished running truncated basis nonanol  \n')

# Wonderful! Now let's run without truncation to compare timings.
# It is advised to check whether basis truncation introduces
# significant changes in total energy

os.chdir('../nonanol_fullbasis')
Projection = ProjectionEmbedding(nonanol,
                                 embed_mask=embed_mask,
                                 calc_base_ll=calc_ll,
                                 calc_base_hl=calc_hl,
                                 mu_val=1.e+6,
                                 truncate_basis=False)

root_print('\nRunning full basis nonanol \n')
start = time.time()

# Now run the simulation!
Projection.run()

end = time.time()
fullbasis_walltime = end - start
fullbasis_energy = Projection.DFT_AinB_total_energy
root_print('Finished running full basis nonanol  \n')

os.chdir('..')


root_print('---------------------------------')
root_print('--------  FINAL ENERGY  ---------')
root_print('---------------------------------')
root_print(f'Truncated basis calc time: {truncated_walltime} s')
root_print(f'Full basis calc time: {fullbasis_walltime} s')
root_print(f'Total time savings: {fullbasis_walltime - truncated_walltime} s')
root_print(f'Total energy (truncated basis): {truncated_energy} eV')
root_print(f'Total energy (full basis): {fullbasis_energy} eV')
root_print(f'Total energy difference: {fullbasis_energy - truncated_energy} eV')
root_print('---------------------------------')
