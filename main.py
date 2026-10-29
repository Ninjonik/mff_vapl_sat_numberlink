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


# =========================================================================
# POMOCNÉ FUNKCIE PRE HRANY
# =========================================================================

def get_neighbors(x, y):
    """
    Vráti zoznam susedov políčka (x, y) v gride.
    """
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            neighbors.append((nx, ny))
    return neighbors


def get_edge_id(x1, y1, x2, y2, offset):
    """
    Vráti ID premennej (neorientovanej) hrany medzi u=(x1, y1) a v=(x2, y2).
    Kde u < v, ak x1+y1 < x2+y2 alebo (ak remíza), tak x1 < x2.
    """
    u, v = (x1, y1), (x2, y2)
    if (x1 + y1 > x2 + y2) or (x1 + y1 == x2 + y2 and x1 > x2):
        u, v = v, u

    ux, uy = u
    vx, vy = v

    if ux == vx:  # Horizontálna
        edge_idx = ux * (GRID_SIZE - 1) + min(uy, vy)
    else:  # Vertikálna
        horiz_count = GRID_SIZE * (GRID_SIZE - 1)
        edge_idx = horiz_count + min(ux, vx) * GRID_SIZE + uy

    return offset + edge_idx + 1


def encode(instance):
    """
    Danú inštanciu Numberlink zakóduje do CNF formule.
    """
    cnf = []

    # Premenné pre políčka
    node_vars_count = CELLS_NUMBER * NUMBERS_LEN

    # Premenné pre (neorientované) hrany
    # Pre N x N grid máme najviac N*(N-1) horizontálnych a N*(N-1) vertikálnych hran
    edge_vars_count = 2 * GRID_SIZE * (GRID_SIZE - 1)

    vars_count = node_vars_count + edge_vars_count

    # ==================================================
    # 1. Práve jedno číslo na políčko
    # ==================================================

    # Každé políčko musí odpovedať aspoň jednému číslu
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            clause = [get_var_is_field_of_number_id(x, y, c) for c in NUMBER_LIST]
            clause.append(0)
            cnf.append(clause)

    # Políčko nemôže odpovedať viac ako jednému číslu
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for i in range(NUMBERS_LEN):
                for j in range(i + 1, NUMBERS_LEN):
                    n1 = NUMBER_LIST[i]
                    n2 = NUMBER_LIST[j]
                    v1 = get_var_is_field_of_number_id(x, y, n1)
                    v2 = get_var_is_field_of_number_id(x, y, n2)
                    cnf.append([-v1, -v2, 0])

    # Koncové body určite musia odpovedať práve svojmu číslu
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            val = instance[x * GRID_SIZE + y]
            if val > 0:
                v = get_var_is_field_of_number_id(x, y, val)
                cnf.append([v, 0])

    # =================================================
    # 2. Podmienky pre hrany medzi vrcholmi a ich čísla
    # =================================================
    # Ak máme hranu E_uv, tak políčka u a v musia mať rovnaké čísla.
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            neighbors = get_neighbors(x, y)
            for nx, ny in neighbors:
                # Aby sme nepridávali každú (neorientovanú) hranu dvakrát
                if (x + y < nx + ny) or (x + y == nx + ny and x < nx):
                    e_var = get_edge_id(x, y, nx, ny, node_vars_count)
                    for c in NUMBER_LIST:
                        u_var = get_var_is_field_of_number_id(x, y, c)
                        v_var = get_var_is_field_of_number_id(nx, ny, c)

                        # E_uv -> (Node_u_c <-> Node_v_c)
                        # 1. (¬E_uv OR ¬Node_u_c OR Node_v_c)
                        cnf.append([-e_var, -u_var, v_var, 0])
                        # 2. (¬E_uv OR ¬Node_v_c OR Node_u_c)
                        cnf.append([-e_var, -v_var, u_var, 0])

    # ==================================================
    # 3. Podmienky pre stupne vrcholov
    # ==================================================
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            val = instance[x * GRID_SIZE + y]
            neighbors = get_neighbors(x, y)
            inc_edges = [get_edge_id(x, y, nx, ny, node_vars_count) for nx, ny in neighbors]

            if val > 0:
                # KONCOVÝ BOD: Stupeň koncového vrcholu musí byť práve 1
                # aspoň jedna hrana
                clause_al1 = inc_edges.copy()
                clause_al1.append(0)
                cnf.append(clause_al1)

                # najviac jedna hrana
                for i in range(len(inc_edges)):
                    for j in range(i + 1, len(inc_edges)):
                        cnf.append([-inc_edges[i], -inc_edges[j], 0])

            else:
                # MEDZIBOD: Stupeň medzivrcholu musí byť práve 2
                # aspoň 2 hrany
                # t.j. ak nejaká hrana neexistuje, tak musí existovať aspoň 1 z ostatných
                for i in range(len(inc_edges)):
                    clause_al2 = [e for j, e in enumerate(inc_edges) if j != i]
                    clause_al2.append(0)
                    cnf.append(clause_al2)

                # najviac 2 hrany
                # t.j. aspoň 1 hrana z ľubovoľnej trojice hrán nesmie existovať
                for i in range(len(inc_edges)):
                    for j in range(i + 1, len(inc_edges)):
                        for k in range(j + 1, len(inc_edges)):
                            cnf.append([-inc_edges[i], -inc_edges[j], -inc_edges[k], 0])

    return cnf, vars_count


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

    node_vars_count = CELLS_NUMBER * NUMBERS_LEN

    for var in model:
        # ignorujeme premenné pre hrany - nie sú potrebné pre výpis
        if 0 < var <= node_vars_count:
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