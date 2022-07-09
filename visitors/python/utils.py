def get_tab(tab: str, level: int, inner=False):
    if inner:
        calc_tab = tab * level if level == 1 else tab * (level - 1)
    else:
        calc_tab = tab * level
    return "{tabulation}".format(
        tabulation=calc_tab
    )
