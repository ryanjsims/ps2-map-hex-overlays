import json

def get_numeric(prompt):
    sign = 1
    val = input(prompt)
    if val.lower().startswith("d"):
        return None
    if val.startswith("-"):
        sign = -1
        val = val[1:]
    while not val.isnumeric():
        sign = 1
        val = input(prompt)
        if val.lower().startswith("d"):
            return None
        if val.startswith("-"):
            sign = -1
            val = val[1:]
    return sign * int(val)
        

def get_hexes():
    r = get_numeric("R? (Blue) ")
    if r is None:
        return []
    s_range = input("S range? (Red)")
    if(s_range.lower().startswith("d")):
        return []
    s_strvals = s_range.split(",")
    s_vals = []
    for val in s_strvals:
        if ":" in val:
            val_range = val.split(":")
            s_vals.extend(range(int(val_range[0]), int(val_range[1]) + 1))
        else:
            s_vals.append(int(val))
    return [(-r-s, r, s) for s in s_vals]
    

with open("oshur_hexes.json") as f:
    facilities: dict = json.load(f)

    
def main():
    for i, facility in enumerate(facilities.values()):
        if len(facility["hexes"]) != 0:
            continue
        print(facility["name"], len(facilities) - i)
        hexes = get_hexes()
        while len(hexes) != 0:
            facility["hexes"].extend(hexes)
            hexes = get_hexes()

    with open("oshur_hexes.json", "w") as f:
        json.dump(facilities, f, indent=4)


if __name__ == "__main__":
    main()
