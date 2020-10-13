rc = {
    "NCSSM A": 760233798880198716,
    "NCSSM B": 760323910197313608, 
    "NCSSM C": 760234102497738764, 
    "NCSSM D": 760324001628160011, 
    "Ravenscroft A": 763231169595703298, 
    "Panther Creek A": 763231344075341845,
    "Panther Creek B": 763231967994314752, 
    "Panther Creek C": 763232157916332055 
}

channels = {
    754144214110961724: 
    {
        "VC": 754139174080217120,
        1: {
            "Team 1": rc["NCSSM A"],
            "Team 2": rc["Panther Creek A"]
        },
        2: {
            "Team 1": rc["NCSSM D"],
            "Team 2": rc["Panther Creek A"]
        },
        3: {
            "Team 1": rc["NCSSM D"],
            "Team 2": rc["Panther Creek B"]
        },
        4: {
            "Team 1": rc["NCSSM C"],
            "Team 2": rc["Panther Creek B"]
        }
    },
    754144225901412462:
    {
        "VC": 754139361246707862,
        1: {
            "Team 1": rc["NCSSM B"],
            "Team 2": rc["Panther Creek B"]
        },
        2: {
            "Team 1": rc["NCSSM A"],
            "Team 2": rc["Panther Creek B"]
        },
        3: {
            "Team 1": rc["NCSSM A"],
            "Team 2": rc["Panther Creek C"]
        },
        4: {
            "Team 1": rc["NCSSM D"],
            "Team 2": rc["Panther Creek C"]
        }
    },
    763236265004367922:
    {
        "VC": 763236343118823435,
        1: {
            "Team 1": rc["NCSSM C"],
            "Team 2": rc["Panther Creek C"]
        },
        2: {
            "Team 1": rc["NCSSM B"],
            "Team 2": rc["Panther Creek C"]
        },
        3: {
            "Team 1": rc["NCSSM B"],
            "Team 2": rc["Ravenscroft A"]
        },
        4: {
            "Team 1": rc["NCSSM A"],
            "Team 2": rc["Ravenscroft A"]
        }
    },
    763236290061533214:
    {
        "VC": 763236378863468554,
        1: {
            "Team 1": rc["NCSSM D"],
            "Team 2": rc["Ravenscroft A"]
        },
        2: {
            "Team 1": rc["NCSSM C"],
            "Team 2": rc["Ravenscroft A"]
        },
        3: {
            "Team 1": rc["NCSSM C"],
            "Team 2": rc["Panther Creek A"]
        },
        4: {
            "Team 1": rc["NCSSM B"],
            "Team 2": rc["Panther Creek A"]
        }
    }    
}