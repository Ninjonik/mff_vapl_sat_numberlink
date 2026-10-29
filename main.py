import subprocess
from argparse import ArgumentParser

GRID_SIZE = 0
NUMBERS = set()
NUMBER_LIST = []
NUMBERS_LEN = 0
CELLS_NUMBER = 0


def load_instance(input_file_name):
    """
    Očakávaný formát:
    - Prvý riadok: veľkosť gridu (GRID_SIZE)
    - Ďalšie riadky: grid (matica) čísel (kde 0 je voľné políčko, čísla = koncové body)
    """
    global GRID_SIZE, NUMBERS, NUMBER_LIST, NUMBERS_LEN, CELLS_NUMBER
    grid = []
    NUMBERS = set()
    with open(input_file_name, "r") as file:
        GRID_SIZE = int(next(file).strip())
        for line in file:
            line = line.split()
            if line:
                row = [int(i) for i in line]
                grid.extend(row)
                for val in row:
                    if val > 0:
                        NUMBERS.add(val)

    NUMBER_LIST = sorted(list(NUMBERS))
    NUMBERS_LEN = len(NUMBER_LIST)
    CELLS_NUMBER = GRID_SIZE * GRID_SIZE
    return grid


def get_var_is_field_of_number_id(x, y, number):
    """
    Vrátí ID premennej pre tvrdenie:
    'políčko na súradniciach (x, y) patrí číslu number'.
    """
    c_idx = NUMBER_LIST.index(number)
    cell_idx = x * GRID_SIZE + y
    return cell_idx * NUMBERS_LEN + c_idx + 1


def decode_var_is_field_of_number_id(var):
    """
    Preloží ID premennej späť na súradnice a číslo.
    """
    zero_based_var = var - 1
    cell_idx = zero_based_var // NUMBERS_LEN
    c_idx = zero_based_var % NUMBERS_LEN

    x = cell_idx // GRID_SIZE
    y = cell_idx % GRID_SIZE
    number = NUMBER_LIST[c_idx]
    return x, y, number


def encode(instance):
    """
    Danú inštanciu Numberlink zakóduje do CNF formule.
    """
    cnf = []

    # Celkový počet premenných:
    # - pre každé políčko a každé číslo máme premennú
    nr_vars = CELLS_NUMBER * NUMBERS_LEN

    # ===========================================
    # PREVOD DO CNF: Práve jedno číslo na políčko
    # ===========================================

    # 1. Každé políčko musí odpovedať aspoň jednému číslu
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            clause = [get_var_is_field_of_number_id(x, y, c) for c in NUMBER_LIST]
            clause.append(0)
            cnf.append(clause)

    # 2. Políčko nemôže odpovedať viac ako jednému číslu
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for i in range(NUMBERS_LEN):
                for j in range(i + 1, NUMBERS_LEN):
                    n1 = NUMBER_LIST[i]
                    n2 = NUMBER_LIST[j]
                    v1 = get_var_is_field_of_number_id(x, y, n1)
                    v2 = get_var_is_field_of_number_id(x, y, n2)
                    # (-v1 OR -v2)
                    cnf.append([-v1, -v2, 0])

    # ------------------------------------------
    # TODO: Ďalšie podmienky
    # ------------------------------------------

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
    print("\n--- DEBUG: Solver return code:", result.returncode)

    # SAT - 10; UNSAT - 20
    if result.returncode == 20:
        print("❌ UNSATISFIABLE")
        return
    elif result.returncode == 10:
        print("✅ SATISFIABLE")
    else:
        print(f"⚠️ ERR: {result.returncode}")
        return

    # Parsovanie modelu z výstupu solvera (riadky začínajúce 'v')
    model = []
    for line in result.stdout.decode('utf-8').split('\n'):
        if line.startswith("v"):
            vars = line.split(" ")
            if "v" in vars:
                vars.remove("v")
            model.extend(int(v) for v in vars if v.strip())
    model.remove(0)  # 0 značí koniec modelu

    print()
    print("##################################################################")
    print("#######[ Human readable result of the Numberlink problem ]########")
    print("##################################################################")
    print()

    print("Pravdivé výroky zo solvera:")
    grid_result = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    for var in model:
        if var > 0:
            x, y, number = decode_var_is_field_of_number_id(var)
            print(f"  Var {var:3d} -> Políčko ({x}, {y}) patrí číslu {number}")
            grid_result[x][y] = number

    print()
    print("Výsledný grid:")
    for x in range(GRID_SIZE):
        print(" ".join(str(grid_result[x][y]) for y in range(GRID_SIZE)))

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