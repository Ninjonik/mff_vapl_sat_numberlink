import subprocess
from argparse import ArgumentParser

GRID_SIZE = 0


def load_instance(input_file_name):
    """
    Očakávaný formát:
    - Prvý riadok: veľkosť gridu (GRID_SIZE)
    - Ďalšie riadky: grid (matica) čísel (kde 0 je voľné políčko, čísla = koncové body)
    """
    global GRID_SIZE
    grid = []
    with open(input_file_name, "r") as file:
        GRID_SIZE = int(next(file).strip())
        for line in file:
            line = line.split()
            if line:
                grid.extend([int(i) for i in line])
    return grid


def encode(instance):
    """
    Danú inštanciu Numberlink zakóduje do CNF formule.
    """
    cnf = []
    nr_vars = 0

    # ==========================================
    # PREVOD DO CNF
    # ==========================================
    # TODO

    return cnf, nr_vars


def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    # Zápis CNF do súboru v DIMACS CNF
    with open(output_name, "w") as file:
        file.write("p cnf " + str(nr_vars) + " " + str(len(cnf)) + '\n')
        for clause in cnf:
            file.write(' '.join(str(lit) for lit in clause) + '\n')

    # Volanie SAT solvera
    return subprocess.run(
        ['./' + solver_name, '-model', '-verb=' + str(verbosity), output_name],
        stdout=subprocess.PIPE
    )


def print_result(result):
    # raw výstup pre debug
    for line in result.stdout.decode('utf-8').split('\n'):
        print(line)

    # SAT - 10; UNSAT - 20)
    if result.returncode == 20:
        return

    # Parsovanie modelu z výstupu solvera (riadky začínajúce 'v')
    model = []
    for line in result.stdout.decode('utf-8').split('\n'):
        if line.startswith("v"):
            vars = line.split(" ")
            vars.remove("v")
            model.extend(int(v) for v in vars)
    model.remove(0) # 0 značí koniec modelu

    print()
    print("##################################################################")
    print("#######[ Human readable result of the Numberlink problem ]########")
    print("##################################################################")
    print()

    # Zakódovanie modelu do gridu
    # TODO


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-i", "--input",
        default="instances/input.in",
        type=str,
        help="The instance file."
    )
    parser.add_argument(
        "-o", "--output",
        default="formula.cnf",
        type=str,
        help="Output file for the DIMACS format (i.e. the CNF formula)."
    )
    parser.add_argument(
        "-s", "--solver",
        default="glucose-syrup",
        type=str,
        help="The SAT solver to be used."
    )
    parser.add_argument(
        "-v", "--verb",
        default=1,
        type=int,
        choices=range(0, 2),
        help="Verbosity of the SAT solver used."
    )
    args = parser.parse_args()

    instance = load_instance(args.input)

    cnf, nr_vars = encode(instance)

    result = call_solver(cnf, nr_vars, args.output, args.solver, args.verb)

    print_result(result)