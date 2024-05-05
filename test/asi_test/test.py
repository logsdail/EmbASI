import sys, os
from glob import glob
import numpy as np
from mpi4py import MPI
from ase.build import molecule
from ase.io import read
from asi4py.asecalc import ASI_ASE_calculator


libaims_path = os.environ["LIBAIMS_PATH"]
print(libaims_path)
lib_names = glob(libaims_path + "/libaims.*so")
print(lib_names)
assert len(lib_names) == 1, lib_names # only one lib should be there
ASI_LIB_PATH = lib_names[0]

def init_via_ase(asi):
  from ase.calculators.aims import Aims
  calc = Aims(xc='PBE', 
    occupation_type="gaussian 0.01",
    mixer="pulay",
    n_max_pulay=10,
    charge_mix_param=0.5,
    sc_accuracy_rho=1E-05,
    sc_accuracy_eev=1E-03,
    sc_accuracy_etot=1E-06,
    sc_accuracy_forces=1E-04,
    sc_iter_limit=100,
    output_level="MD_light",
    compute_forces=True,
    postprocess_anyway = True,
    density_update_method='density_matrix', # for DM export
  )
  calc.write_input(asi.atoms)

atoms = read('input/geometry.in')

atoms.calc = ASI_ASE_calculator(ASI_LIB_PATH, init_via_ase, MPI.COMM_WORLD, atoms, work_dir="./", logfile="aims.out")
#atoms.calc.asi.keep_overlap = True
#atoms.calc.asi.keep_hamiltonian = True
#atoms.calc.asi.keep_density_matrix = True
atoms.calc.asi.init_density_matrix = {(1,1):np.loadtxt('DM_9.txt').T}

E = atoms.get_potential_energy()
forces = atoms.get_forces()
if MPI.COMM_WORLD.Get_rank() == 0:
  print(f'Potential energy: {E:.5f}')
  print(f'Forces:')
  np.savetxt(sys.stdout, forces, fmt="%10.6f")
if ((1,1) in atoms.calc.asi.dm_storage):
  print(f'Nel: {np.sum(atoms.calc.asi.dm_storage[(1,1)] * atoms.calc.asi.overlap_storage[(1,1)])}')
  print(f'HD: {np.sum(atoms.calc.asi.dm_storage[(1,1)] * atoms.calc.asi.hamiltonian_storage[(1,1)])}')
